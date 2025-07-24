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
DIRETORIO_PYTHON_WIDGET = os.path.join(DIRETORIO_APP_DATA, "python_widget_env")
REGISTRO_WIDGET = r"Software\Microsoft\Windows\CurrentVersion\Run"
CHAVE_REGISTRO_WIDGET = "FCT_UFG_DesktopInfo"

# Conteúdo do script do widget (sem alterações)
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
    """Executa um comando PowerShell."""
    yield f"Executando via PowerShell: {comando[:70]}..."
    try:
        processo = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando],
            capture_output=True, text=True, encoding='utf-8', errors='ignore',
            timeout=timeout, check=False
        )
        if processo.stdout:
            yield processo.stdout.strip()
        if processo.returncode != 0:
            yield f"ERRO: Código de retorno {processo.returncode}."
            if processo.stderr:
                yield f"Detalhes: {processo.stderr.strip()}"
    except Exception as e:
        yield f"ERRO CRÍTICO (PowerShell): {e}"

def executar_comando_cmd(comando, timeout=180, work_dir=None):
    """Executa um comando no CMD, com opção de diretório de trabalho."""
    yield f"Executando via CMD: {comando[:70]}..."
    try:
        processo = subprocess.run(
            ["cmd", "/c", comando],
            capture_output=True, text=True, encoding='oem', errors='ignore',
            timeout=timeout, check=False, cwd=work_dir,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if processo.stdout:
            yield processo.stdout.strip()
        if processo.returncode != 0:
            yield f"AVISO: Código de retorno {processo.returncode}."
            if processo.stderr:
                yield f"Saída de erro: {processo.stderr.strip()}"
    except Exception as e:
        yield f"ERRO CRÍTICO (CMD): {e}"

def baixar_recursos_necessarios(url_repositorio):
    """Baixa os arquivos de configuração (GPOs, Tema) do GitHub."""
    arquivos_para_baixar = ["lgpo.exe", "machine.txt", "user.txt", "fct-labs.deskthemepack"]
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
            yield f"'{arquivo}' baixado com sucesso."
        except requests.exceptions.RequestException as e:
            yield f"ERRO CRÍTICO ao baixar '{arquivo}': {e}"
            return
    yield "Download de todos os recursos concluído."

def gerenciar_widget_desktop(acao, config):
    """Adiciona ou remove o widget de aviso do desktop."""
    pythonw_exe = os.path.join(DIRETORIO_PYTHON_WIDGET, 'pythonw.exe')
    comando_finalizar = f'taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq WidgetInfo*"'

    if acao == 'adicionar':
        url_python_widget = config.get("URL_PYTHON_WIDGET")
        if not url_python_widget:
            yield "ERRO CRÍTICO: URL para o ambiente Python do widget não configurada."
            return
        zip_path = os.path.join(DIRETORIO_APP_DATA, "python_widget_env.zip")
        yield f"Baixando ambiente Python do widget..."
        try:
            with requests.get(url_python_widget, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(zip_path, 'wb') as f: shutil.copyfileobj(r.raw, f)
        except requests.exceptions.RequestException as e:
            yield f"ERRO CRÍTICO ao baixar o ambiente do widget: {e}"; return
        yield "Extraindo ambiente Python..."
        try:
            if os.path.exists(DIRETORIO_PYTHON_WIDGET): shutil.rmtree(DIRETORIO_PYTHON_WIDGET)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(DIRETORIO_PYTHON_WIDGET)
            os.remove(zip_path)
        except Exception as e:
            yield f"ERRO CRÍTICO ao extrair o ambiente do widget: {e}"; return
        if not os.path.exists(pythonw_exe):
            yield f"ERRO CRÍTICO: 'pythonw.exe' não encontrado após extração."; return
        yield "Ambiente do widget instalado."
        yield f"Criando script do widget..."
        with open(CAMINHO_SCRIPT_WIDGET, "w", encoding="utf-8") as f: f.write(CONTEUDO_SCRIPT_WIDGET)
        yield "Adicionando à inicialização do Windows..."
        try:
            comando_reg = f'"{pythonw_exe}" "{CAMINHO_SCRIPT_WIDGET}"'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRO_WIDGET, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, CHAVE_REGISTRO_WIDGET, 0, winreg.REG_SZ, comando_reg)
            yield "Widget configurado para iniciar com o Windows."
        except Exception as e:
            yield f"ERRO ao registrar na inicialização: {e}"; return
        yield "Finalizando instâncias antigas e iniciando o widget..."
        subprocess.run(comando_finalizar, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.Popen([pythonw_exe, CAMINHO_SCRIPT_WIDGET], creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Widget adicionado e iniciado com sucesso."
    elif acao == 'remover':
        yield "Finalizando processo do widget..."
        subprocess.run(comando_finalizar, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Removendo da inicialização do Windows..."
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRO_WIDGET, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, CHAVE_REGISTRO_WIDGET)
            yield "Registro de inicialização removido."
        except FileNotFoundError: yield "AVISO: Registro de inicialização não encontrado."
        except Exception as e: yield f"ERRO ao remover do registro: {e}"
        if os.path.exists(CAMINHO_SCRIPT_WIDGET):
            try: os.remove(CAMINHO_SCRIPT_WIDGET); yield "Arquivo de script removido."
            except OSError as e: yield f"ERRO ao remover arquivo de script: {e}"
        if os.path.exists(DIRETORIO_PYTHON_WIDGET):
            try: shutil.rmtree(DIRETORIO_PYTHON_WIDGET); yield "Ambiente Python do widget removido."
            except OSError as e: yield f"ERRO ao remover diretório do widget: {e}"
        yield "Widget removido com sucesso."

def garantir_permissoes_de_tema():
    """Verifica e remove explicitamente a política de restrição de temas no Registro do Windows."""
    yield "Verificando permissões de alteração de tema no Registro..."
    chave_reg_caminho = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
    nome_valor = "NoThemes"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, chave_reg_caminho, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, nome_valor)
                yield f"Política de bloqueio de tema encontrada e removida do Registro (HKLM)."
            except FileNotFoundError:
                yield f"Nenhuma política de bloqueio de tema encontrada no Registro (HKLM)."
            except Exception as e_del:
                yield f"AVISO: Não foi possível remover a chave '{nome_valor}' do Registro (HKLM): {e_del}"
    except FileNotFoundError:
        yield "Caminho de política de tema não existe no Registro (HKLM), o que é bom."
    except Exception as e_open:
        yield f"ERRO ao acessar o Registro (HKLM) para verificar políticas de tema: {e_open}"

def aplicar_tema_fct(caminho_tema):
    """Aplica o tema visual da FCT delegando a ação para o shell do usuário (explorer.exe)."""
    yield from garantir_permissoes_de_tema()
    yield f"Verificando tema em: {caminho_tema}"
    if not os.path.exists(caminho_tema):
        yield f"ERRO: Arquivo de tema não encontrado: {caminho_tema}."
        yield "Dica: Use a opção 'Baixar Recursos FCT' para obter os arquivos necessários."
        return
    try:
        comando = f'explorer.exe "{caminho_tema}"'
        yield f"Enviando comando de aplicação de tema ao shell do usuário: {comando}"
        subprocess.run(
            comando, shell=True, check=False, creationflags=subprocess.CREATE_NO_WINDOW
        )
        yield "Comando para aplicar o tema foi enviado com sucesso."
        yield "A alteração pode levar alguns segundos e pode exigir confirmação do usuário."
    except Exception as e:
        yield f"ERRO CRÍTICO ao tentar aplicar o tema via explorer: {e}"

def aplicar_gpos_fct(caminho_base_gpo):
    """Aplica as políticas de grupo (GPOs) da FCT usando lgpo.exe."""
    arquivos_necessarios = [
        os.path.join(caminho_base_gpo, "lgpo.exe"),
        os.path.join(caminho_base_gpo, "machine.txt"),
        os.path.join(caminho_base_gpo, "user.txt")
    ]
    yield "Verificando arquivos de GPO necessários..."
    if not all(os.path.exists(p) for p in arquivos_necessarios):
        yield f"ERRO: Arquivos de GPO não encontrados em {caminho_base_gpo}."
        return
    
    diretorio_original = os.getcwd()
    try:
        os.chdir(caminho_base_gpo)
        yield "Aplicando política de máquina..."
        yield from executar_comando_cmd(r"lgpo.exe /t machine.txt")
        yield "Aplicando política de usuário..."
        yield from executar_comando_cmd(r"lgpo.exe /t user.txt")
        yield "Comandos de aplicação de GPOs da FCT enviados."
    except Exception as e:
        yield f"ERRO ao executar aplicação de GPO: {e}"
    finally:
        os.chdir(diretorio_original)

# CORRIGIDO: BleachBit agora é salvo em ProgramData
def iniciar_limpeza_sistema(url_ferramenta):
    """Baixa e executa o BleachBit para limpeza geral do sistema."""
    # O diretório base agora é o mesmo da aplicação
    base_dir = DIRETORIO_APP_DATA
    tool_dir = os.path.join(base_dir, "BleachBit")
    zip_path = os.path.join(base_dir, "BleachBit.zip")
    try:
        yield f"Baixando BleachBit para {base_dir}..."
        with requests.get(url_ferramenta, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f: shutil.copyfileobj(r.raw, f)
        yield f"Extraindo para {tool_dir}..."
        if os.path.exists(tool_dir): shutil.rmtree(tool_dir)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(tool_dir)
        yield "Procurando por bleachbit_console.exe..."
        caminho_executavel = next((os.path.join(r, f) for r, _, fs in os.walk(tool_dir) for f in fs if f == "bleachbit_console.exe"), None)
        if not caminho_executavel:
            yield "ERRO: bleachbit_console.exe não encontrado após a extração."; return
        yield f"Executável encontrado: {caminho_executavel}"
        yield "Listando limpadores disponíveis..."
        list_process = subprocess.run([caminho_executavel, "--list-cleaners"], capture_output=True, text=True, check=True)
        all_cleaners = list_process.stdout.split()
        cleaners_to_run = [c for c in all_cleaners if not c.startswith("deep_scan.") and c != "system.free_disk_space"]
        yield f"{len(cleaners_to_run)} limpadores selecionados. AVISO: A limpeza pode demorar."
        yield "Executando limpeza com BleachBit..."
        subprocess.run([caminho_executavel, "--clean"] + cleaners_to_run, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Limpeza completa concluída!"
    except Exception as e:
        yield f"ERRO durante a limpeza: {e}"
    finally:
        # A limpeza dos arquivos baixados continua sendo uma boa prática
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
    yield from executar_comando_cmd("gpupdate /force", timeout=120)
    yield "Restauração das GPOs padrão concluída."

def resetar_microsoft_store():
    """Limpa o cache e re-registra a Microsoft Store."""
    yield "Iniciando reset da Microsoft Store..."
    yield from executar_comando_cmd("wsreset.exe -q", timeout=120)
    yield "Comando de limpeza de cache enviado."
    yield "Re-registrando o aplicativo da Store..."
    comando = 'Get-AppxPackage *WindowsStore* -AllUsers | ForEach-Object {Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml"}'
    yield from executar_comando_powershell(comando)
    yield "Comando de re-registro enviado."

def forcar_atualizacao_gpos():
    """Força a atualização das Políticas de Grupo (gpupdate)."""
    yield "Forçando atualização das Políticas de Grupo (GPOs)..."
    yield from executar_comando_cmd("gpupdate /force", timeout=120)
    yield "Tentativa de atualização de GPO concluída."

# CORRIGIDO: Usa um arquivo temporário para obter o nome de usuário com acentos.
def limpar_pastas_usuario():
    """Limpa as pastas Desktop e Downloads do usuário, lidando com acentos."""
    yield "Iniciando limpeza de pastas do usuário..."
    temp_file = os.path.join(os.environ['TEMP'], 'current_user.tmp')
    # Comando PowerShell para salvar o nome de usuário em um arquivo com codificação UTF-8
    comando_ps = f"(Get-CimInstance -ClassName Win32_ComputerSystem).Username | Out-File -FilePath '{temp_file}' -Encoding utf8 -NoNewline"
    
    try:
        # Executa o comando para criar o arquivo
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando_ps],
            check=True, capture_output=True
        )

        # Lê o nome do usuário do arquivo com a codificação correta
        if not os.path.exists(temp_file):
            yield "ERRO: Arquivo temporário de usuário não foi criado."
            return
            
        with open(temp_file, 'r', encoding='utf-8') as f:
            nome_usuario_completo = f.read().strip()

        if not nome_usuario_completo:
            yield "ERRO: Não foi possível determinar o usuário logado."
            return
        
        nome_usuario = nome_usuario_completo.split('\\')[-1]
        yield f"Usuário ativo encontrado: {nome_usuario}"

        caminho_base_usuario = os.path.join("C:\\Users", nome_usuario)
        pastas_para_limpar = {
            "Desktop": os.path.join(caminho_base_usuario, "Desktop"),
            "Downloads": os.path.join(caminho_base_usuario, "Downloads")
        }
        itens_a_preservar = ('.lnk', '.url', '.ini')

        for nome_pasta, caminho_pasta in pastas_para_limpar.items():
            yield f"--- Limpando a pasta {nome_pasta} ---"
            if not os.path.exists(caminho_pasta):
                yield f"AVISO: Pasta não encontrada: {caminho_pasta}"
                continue
            for item in os.listdir(caminho_pasta):
                caminho_completo = os.path.join(caminho_pasta, item)
                if nome_pasta == "Desktop" and item.lower().endswith(itens_a_preservar):
                    yield f"Preservando: {item}"
                    continue
                try:
                    if os.path.isfile(caminho_completo) or os.path.islink(caminho_completo):
                        os.unlink(caminho_completo)
                    elif os.path.isdir(caminho_completo):
                        shutil.rmtree(caminho_completo)
                    yield f"Item removido: {item}"
                except Exception as e:
                    yield f"ERRO ao remover '{item}': {e}"
            yield f"Limpeza da pasta {nome_pasta} concluída."

    except subprocess.CalledProcessError as e:
        yield f"ERRO CRÍTICO ao obter nome do usuário: {e}"
        if e.stderr:
            yield f"Detalhes do erro do PowerShell: {e.stderr.decode('utf-8', 'ignore')}"
    except Exception as e:
        yield f"ERRO CRÍTICO ao limpar pastas do usuário: {e}"
    finally:
        # Garante que o arquivo temporário seja sempre removido
        if os.path.exists(temp_file):
            os.remove(temp_file)

def manutencao_preventiva_1_click(config):
    """Executa uma sequência de tarefas de manutenção preventiva."""
    yield "--- INICIANDO MANUTENÇÃO PREVENTIVA COMPLETA ---"
    yield "\nPASSO 1/9: Baixando recursos da FCT..."
    yield from baixar_recursos_necessarios(config['URL_REPOSITORIO_FCT'])
    yield "\nPASSO 2/9: Restaurando GPOs Padrão..."
    yield from restaurar_gpos_padrao()
    yield "\nPASSO 3/9: Forçando Atualização de GPOs..."
    yield from forcar_atualizacao_gpos()
    yield "\nPASSO 4/9: Limpeza Geral do Sistema..."
    yield from iniciar_limpeza_sistema(config['URL_BLEACHBIT'])
    yield "\nPASSO 5/9: Limpando pastas do Usuário..."
    yield from limpar_pastas_usuario()
    yield "\nPASSO 6/9: Aplicando Tema Visual da FCT..."
    yield from aplicar_tema_fct(config['CAMINHO_TEMA'])
    yield "\nPASSO 7/9: Aplicando GPOs da FCT..."
    yield from aplicar_gpos_fct(config['CAMINHO_BASE_GPO'])
    yield "\nPASSO 8/9: Forçando atualização de GPO novamente..."
    yield from forcar_atualizacao_gpos()
    yield "\nPASSO 9/9: Resetando a Microsoft Store..."
    yield from resetar_microsoft_store()
    yield "\n--- MANUTENÇÃO PREVENTIVA CONCLUÍDA ---"
    yield "É recomendado reiniciar o computador para que todas as alterações tenham efeito."