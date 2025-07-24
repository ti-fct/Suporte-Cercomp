# backend.py
import os
import subprocess
import shutil
import json
import requests
import zipfile
import winreg
import sys
import time

# --- Constantes de Configuração ---
DIRETORIO_APP_DATA = r"C:\ProgramData\Suporte-Cercomp"
DIRETORIO_LOGS = os.path.join(DIRETORIO_APP_DATA, "logs")
ARQUIVO_CONFIG = os.path.join(DIRETORIO_APP_DATA, "config.json")
CAMINHO_SCRIPT_WIDGET = os.path.join(DIRETORIO_APP_DATA, "AvisoDesktop.pyw")
REGISTRO_WIDGET = r"Software\Microsoft\Windows\CurrentVersion\Run"
CHAVE_REGISTRO_WIDGET = "FCT_UFG_DesktopInfo"

# Conteúdo do script que será criado para o widget do desktop
CONTEUDO_SCRIPT_WIDGET = """
# Aviso Desktop
import sys
import socket
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
    from PyQt6.QtCore import Qt, QEvent, QTimer
    from PyQt6.QtGui import QColor
except ImportError:
    sys.exit()

class WidgetInfo(QWidget):
    def __init__(self):
        super().__init__()
        self.configurar_interface()

    def configurar_interface(self):
        self.setWindowTitle("WidgetInfo")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnBottomHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.rotulo = QLabel(self)
        self.rotulo.setText(self.formatar_texto())
        self.rotulo.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.rotulo.setStyleSheet("QLabel { color: white; font-size: 11pt; }")

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(5)
        sombra.setOffset(2, 2)
        sombra.setColor(QColor(0, 0, 0))
        self.rotulo.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self)
        layout.addWidget(self.rotulo)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        self.adjustSize()
        self.posicionar_widget()

    def formatar_texto(self):
        nome_computador = socket.gethostname()
        texto = (
            "<p style='margin:0; text-align:right; color:white;'>"
            "<b>💻 LAB. DE INFORMÁTICA - FCT/UFG</b><br>"
            "───────────────────────────<br>"
            f"{nome_computador}<br><br>"
            "<b>📜 REGRAS DE USO</b><br>"
            "🎓 Uso exclusivo para atividades acadêmicas<br>"
            "🚫 Não consumir alimentos no laboratório<br>"
            "⚙️ Não alterar configurações do sistema<br><br>"
            "<b>🚪 PROCEDIMENTOS AO SAIR</b><br>"
            "💾 Remova dispositivos externos<br>"
            "❌ Encerre todos os aplicativos<br>"
            "🔒 Faça logout das contas<br><br>"
            "<b>🛠️ SUPORTE TÉCNICO</b><br>"
            "🌐 chamado.ufg.br<br>"
            "💬 (62) 3209-6555"
            "</p>"
        )
        return texto

    def posicionar_widget(self):
        tela = QApplication.primaryScreen()
        if tela:
            retangulo_disponivel = tela.availableGeometry()
            margem = 20
            x = retangulo_disponivel.right() - self.width() - margem
            y = retangulo_disponivel.top() + margem
            self.move(x, y)

    def changeEvent(self, evento):
        if evento.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                QTimer.singleShot(0, self.showNormal)
        super().changeEvent(evento)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = WidgetInfo()
    widget.show()
    sys.exit(app.exec())
"""

# --- Funções Lógicas ---

def executar_comando_powershell(comando, timeout=180):
    """Executa um comando PowerShell com timeout e retorna o resultado."""
    yield f"Executando (timeout: {timeout}s): {comando[:70]}..."
    try:
        processo = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando],
            capture_output=True, text=True, encoding='utf-8', errors='ignore',
            timeout=timeout, check=False
        )
        if processo.stdout:
            yield processo.stdout.strip()
        if processo.returncode != 0:
            yield f"ERRO: Comando retornou código {processo.returncode}."
            if processo.stderr:
                yield f"Detalhes do erro: {processo.stderr.strip()}"
    except subprocess.TimeoutExpired:
        yield f"ERRO: O comando excedeu o tempo limite de {timeout} segundos."
    except Exception as e:
        yield f"ERRO CRÍTICO ao executar PowerShell: {e}"

def baixar_recursos_necessarios(url_repositorio):
    """Baixa os arquivos de configuração (GPOs, Tema) do GitHub."""
    arquivos_para_baixar = [
        "lgpo.exe",
        "machine.txt",
        "user.txt",
        "fct-labs.deskthemepack"
    ]
    yield "Verificando e baixando recursos necessários..."
    
    if not url_repositorio.endswith('/'):
        url_repositorio += '/'

    for arquivo in arquivos_para_baixar:
        url_arquivo = url_repositorio + arquivo
        caminho_destino = os.path.join(DIRETORIO_APP_DATA, arquivo)
        yield f"Baixando '{arquivo}'..."
        try:
            with requests.get(url_arquivo, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(caminho_destino, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            yield f"'{arquivo}' baixado com sucesso para {caminho_destino}"
        except requests.exceptions.RequestException as e:
            yield f"ERRO CRÍTICO ao baixar '{arquivo}': {e}"
            yield "Verifique a URL nas configurações e a conexão com a internet."
            return # Interrompe se um arquivo essencial não puder ser baixado
    yield "Download de todos os recursos concluído."

def gerenciar_widget_desktop(acao, config):
    """Adiciona ou remove o widget de aviso do desktop, gerenciando o processo."""
    python_exe = sys.executable
    pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')

    if not os.path.exists(pythonw_exe):
        pythonw_exe = shutil.which('pythonw.exe')
        if not pythonw_exe:
            yield "ERRO CRÍTICO: pythonw.exe não foi encontrado."
            return

    # --- LÓGICA DE GERENCIAMENTO DO PROCESSO ---
    comando_finalizar = 'taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq WidgetInfo*"'

    if acao == 'adicionar':
        # Instalação de dependências (se necessário)
        dependencia = "PyQt6"
        yield f"Verificando dependência: {dependencia}..."
        try:
            subprocess.check_call([python_exe, "-m", f"import {dependencia}"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            yield f"'{dependencia}' já está instalada."
        except subprocess.CalledProcessError:
            yield f"'{dependencia}' não encontrada. Instalando..."
            resultado_pip = subprocess.run([python_exe, "-m", "pip", "install", dependencia],
                                           capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if resultado_pip.returncode != 0:
                yield f"ERRO ao instalar '{dependencia}'. Verifique a internet."
                yield resultado_pip.stderr
                return
            yield f"'{dependencia}' instalada com sucesso."

        # Criação do script e registro na inicialização
        yield f"Criando script do widget em {CAMINHO_SCRIPT_WIDGET}..."
        with open(CAMINHO_SCRIPT_WIDGET, "w", encoding="utf-8") as f:
            f.write(CONTEUDO_SCRIPT_WIDGET)

        yield "Adicionando à inicialização do Windows..."
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRO_WIDGET, 0, winreg.KEY_SET_VALUE) as key:
                comando = f'"{pythonw_exe}" "{CAMINHO_SCRIPT_WIDGET}"'
                winreg.SetValueEx(key, CHAVE_REGISTRO_WIDGET, 0, winreg.REG_SZ, comando)
            yield "Widget configurado para iniciar com o Windows para todos os usuários."
        except Exception as e:
            yield f"ERRO ao registrar na inicialização: {e}"

        yield "Verificando se o widget já está ativo..."
        # Finaliza qualquer instância antiga para garantir um início limpo
        subprocess.run(comando_finalizar, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Iniciando o widget na área de trabalho..."
        subprocess.Popen([pythonw_exe, CAMINHO_SCRIPT_WIDGET], creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Widget adicionado e iniciado com sucesso."

    elif acao == 'remover':
        yield "Finalizando processo do widget, se estiver ativo..."
        # Adicionamos a captura de resultado para dar um feedback melhor
        resultado_kill = subprocess.run(
            comando_finalizar,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if "SUCESSO" in resultado_kill.stdout:
            yield "Processo do widget finalizado com sucesso."
        else:
            yield "Nenhum processo do widget encontrado para finalizar (o que é normal se não estiver visível)."

        yield "Removendo da inicialização do Windows (de Todos os Usuários)..."
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRO_WIDGET, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, CHAVE_REGISTRO_WIDGET)
            yield "Registro de inicialização removido."
        except FileNotFoundError:
            yield "AVISO: Registro de inicialização não foi encontrado (pode já ter sido removido)."
        except PermissionError:
            yield "ERRO DE PERMISSÃO: Não foi possível remover a chave do registro HKLM. Verifique se a aplicação está como Admin."
        except Exception as e:
            yield f"ERRO ao remover do registro: {e}"

        if os.path.exists(CAMINHO_SCRIPT_WIDGET):
            try:
                os.remove(CAMINHO_SCRIPT_WIDGET)
                yield "Arquivo de script removido."
            except OSError as e:
                yield f"ERRO ao remover arquivo de script: {e}"

        yield "Widget removido com sucesso."


def aplicar_tema_fct(caminho_tema):
    """Aplica o tema visual da FCT a partir de um arquivo local."""
    yield f"Verificando tema em: {caminho_tema}"
    if not os.path.exists(caminho_tema):
        yield f"ERRO: Arquivo de tema não encontrado: {caminho_tema}."
        yield "Execute a 'Manutenção 1 Click' ou baixe os recursos para obtê-lo."
        return
    try:
        os.startfile(caminho_tema)
        yield "Comando para aplicar o tema foi enviado ao Windows."
    except Exception as e:
        yield f"ERRO CRÍTICO ao tentar aplicar o tema: {e}"

def aplicar_gpos_fct(caminho_base_gpo):
    """Aplica as políticas de grupo (GPOs) da FCT usando arquivos locais."""
    lgpo_path = os.path.join(caminho_base_gpo, "lgpo.exe")
    machine_txt_path = os.path.join(caminho_base_gpo, "machine.txt")
    user_txt_path = os.path.join(caminho_base_gpo, "user.txt")

    yield "Verificando arquivos de GPO necessários..."
    if not all(os.path.exists(p) for p in [lgpo_path, machine_txt_path, user_txt_path]):
        yield f"ERRO: Arquivos de GPO não encontrados em {caminho_base_gpo}."
        yield "Execute a 'Manutenção 1 Click' ou baixe os recursos para obtê-los."
        return

    yield "Aplicando política de máquina..."
    subprocess.run([lgpo_path, "/t", machine_txt_path], capture_output=True)
    yield "Aplicando política de usuário..."
    subprocess.run([lgpo_path, "/t", user_txt_path], capture_output=True)
    yield "GPOs da FCT aplicadas com sucesso."

def iniciar_limpeza_sistema(url_ferramenta):
    """Baixa e executa o BleachBit para limpeza geral do sistema."""
    temp_dir = os.environ.get("TEMP", r"C:\Windows\Temp")
    tool_dir = os.path.join(temp_dir, "BleachBit")
    zip_path = os.path.join(temp_dir, "BleachBit.zip")

    try:
        # Etapa 1: Download e extração
        yield f"Baixando BleachBit de {url_ferramenta}..."
        with requests.get(url_ferramenta, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        yield f"Extraindo para {tool_dir}..."
        # Garante que o diretório esteja limpo antes de extrair
        if os.path.exists(tool_dir):
            shutil.rmtree(tool_dir)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tool_dir)

        yield "Procurando por bleachbit_console.exe..."
        caminho_executavel = None
        for root, dirs, files in os.walk(tool_dir):
            if "bleachbit_console.exe" in files:
                caminho_executavel = os.path.join(root, "bleachbit_console.exe")
                yield f"Executável encontrado em: {caminho_executavel}"
                break
        
        if not caminho_executavel:
            yield "ERRO: bleachbit_console.exe não encontrado após a extração. A estrutura do ZIP pode ter mudado."
            return

        yield "Listando limpadores disponíveis..."
        list_process = subprocess.run(
            [caminho_executavel, "--list-cleaners"],
            capture_output=True, text=True, check=True
        )
        all_cleaners = list_process.stdout.split()

        # Exclui limpadores de 'deep scan' e 'free disk space'
        cleaners_to_run = [
            c for c in all_cleaners
            if not c.startswith("deep_scan.") and c != "system.free_disk_space"
        ]

        yield f"{len(cleaners_to_run)} limpadores selecionados para execução."
        yield "AVISO: A limpeza pode demorar vários minutos."
        yield "Executando limpeza com BleachBit..."

        subprocess.run(
            [caminho_executavel, "--clean"] + cleaners_to_run,
            check=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        yield "Limpeza completa concluída!"

    except Exception as e:
        yield f"ERRO durante a limpeza: {e}"
    finally:
        # Limpeza dos arquivos temporários
        if os.path.exists(tool_dir): shutil.rmtree(tool_dir, ignore_errors=True)
        if os.path.exists(zip_path): os.remove(zip_path)

def renomear_computador(novo_nome):
    """Altera o nome do computador no sistema."""
    yield f"Tentando alterar o nome para '{novo_nome}'..."
    yield from executar_comando_powershell(f'Rename-Computer -NewName "{novo_nome}" -Force -ErrorAction Stop')
    yield "Nome alterado! É necessário reiniciar para aplicar."

def restaurar_gpos_padrao():
    """Remove as políticas locais e força a atualização."""
    caminhos_gpo = [
        os.path.join(os.environ['WINDIR'], 'System32', 'GroupPolicy'),
        os.path.join(os.environ['WINDIR'], 'System32', 'GroupPolicyUsers')
    ]
    for path in caminhos_gpo:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                yield f"Removido: {path}"
            except Exception as e:
                yield f"ERRO ao remover {path}: {e}"
    yield from executar_comando_powershell("gpupdate /force", timeout=120)
    yield "Restauração das GPOs padrão concluída."

def resetar_microsoft_store():
    """Limpa o cache e re-registra a Microsoft Store."""
    yield "Iniciando reset da Microsoft Store..."
    try:
        subprocess.run(["wsreset.exe"], check=True, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Cache da loja limpo."
    except Exception as e:
        yield f"AVISO: Falha no wsreset.exe: {e}"

    yield "Re-registrando o aplicativo da Store..."
    comando = 'Get-AppxPackage *WindowsStore* -AllUsers | ForEach-Object {Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml"}'
    yield from executar_comando_powershell(comando)
    yield "Comando de re-registro enviado."

def forcar_atualizacao_gpos():
    """Força a atualização das Políticas de Grupo (gpupdate)."""
    yield "Forçando atualização das Políticas de Grupo (GPOs)..."
    yield from executar_comando_powershell("gpupdate /force", timeout=120)
    yield "Tentativa de atualização de GPO concluída."

def limpar_pastas_usuario():
    """
    Limpa as pastas Desktop e Downloads do usuário interativo atual.
    No Desktop, preserva atalhos (.lnk, .url) e arquivos de configuração.
    """
    yield "Iniciando limpeza de pastas do usuário..."
    comando_ps = "(qwinsta | where {$_ -match ' active.*console'}) -replace ' +',',' | ForEach-Object { (($_ -split ',')[2]) }"
    try:
        # Encontra o nome do usuário da sessão ativa (console)
        processo = subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando_ps],
            capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore'
        )
        nome_usuario = processo.stdout.strip()
        if not nome_usuario or nome_usuario == 'services':
            yield "ERRO: Não foi possível determinar o usuário logado na sessão ativa."
            return

        yield f"Usuário ativo encontrado: {nome_usuario}"
        caminho_base_usuario = os.path.join("C:\\Users", nome_usuario)
        pastas_para_limpar = {
            "Desktop": os.path.join(caminho_base_usuario, "Desktop"),
            "Downloads": os.path.join(caminho_base_usuario, "Downloads")
        }
        itens_a_preservar = ('.lnk', '.url', '.ini') # Extensões e arquivos a ignorar

        for nome_pasta, caminho_pasta in pastas_para_limpar.items():
            yield f"--- Limpando a pasta {nome_pasta} ---"
            if not os.path.exists(caminho_pasta):
                yield f"AVISO: Pasta não encontrada: {caminho_pasta}"
                continue

            for item in os.listdir(caminho_pasta):
                caminho_completo = os.path.join(caminho_pasta, item)
                
                # Regra especial para o Desktop: não excluir ícones
                if nome_pasta == "Desktop" and item.lower().endswith(itens_a_preservar):
                    yield f"Preservando ícone/config: {item}"
                    continue
                
                try:
                    if os.path.isfile(caminho_completo) or os.path.islink(caminho_completo):
                        os.unlink(caminho_completo)
                        yield f"Arquivo removido: {item}"
                    elif os.path.isdir(caminho_completo):
                        shutil.rmtree(caminho_completo)
                        yield f"Diretório removido: {item}"
                except Exception as e:
                    yield f"ERRO ao remover '{item}': {e}"
            yield f"Limpeza da pasta {nome_pasta} concluída."

    except Exception as e:
        yield f"ERRO CRÍTICO ao tentar limpar pastas do usuário: {e}"


def manutencao_preventiva_1_click(config):
    """
    Executa uma sequência de tarefas de manutenção preventiva em uma única ação.
    """
    yield "--- INICIANDO MANUTENÇÃO PREVENTIVA COMPLETA ---"
    
    yield "\nPASSO 1/8: Baixando recursos da FCT (GPOs, Tema)..."
    yield from baixar_recursos_necessarios(config['URL_REPOSITORIO_FCT'])

    yield "\nPASSO 2/8: Restaurando GPOs Padrão..."
    yield from restaurar_gpos_padrao()

    yield "\nPASSO 3/8: Forçando Atualização das GPOs..."
    yield from forcar_atualizacao_gpos()

    yield "\nPASSO 4/8: Iniciando Limpeza Geral do Sistema com BleachBit..."
    yield from iniciar_limpeza_sistema(config['URL_BLEACHBIT'])

    yield "\nPASSO 5/8: Limpando pastas Desktop e Downloads do Usuário..."
    yield from limpar_pastas_usuario()

    yield "\nPASSO 6/8: Aplicando Tema Visual da FCT..."
    yield from aplicar_tema_fct(config['CAMINHO_TEMA'])

    yield "\nPASSO 7/8: Aplicando Políticas de Grupo (GPOs) da FCT..."
    yield from aplicar_gpos_fct(config['CAMINHO_BASE_GPO'])

    yield "\nPASSO 8/8: Forçando atualização de GPO novamente para garantir aplicação..."
    yield from forcar_atualizacao_gpos()
    
    yield "\nPASSO 9/9: Resetando a Microsoft Store..."
    yield from resetar_microsoft_store()

    yield "\n--- MANUTENÇÃO PREVENTIVA CONCLUÍDA ---"
    yield "É recomendado reiniciar o computador para que todas as alterações tenham efeito."