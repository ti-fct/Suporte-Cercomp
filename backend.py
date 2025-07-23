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
DIRETORIO_APP_DATA = r"C:\ProgramData\ManutencaoUFG"
DIRETORIO_LOGS = os.path.join(DIRETORIO_APP_DATA, "logs")
ARQUIVO_CONFIG = os.path.join(DIRETORIO_APP_DATA, "config.json")
CAMINHO_SCRIPT_WIDGET = os.path.join(DIRETORIO_APP_DATA, "AvisoDesktop.pyw")
REGISTRO_WIDGET = r"Software\Microsoft\Windows\CurrentVersion\Run"
CHAVE_REGISTRO_WIDGET = "FCT_UFG_DesktopInfo"

# Conteúdo do script que será criado para o widget do desktop
CONTEUDO_SCRIPT_WIDGET = """
# (O conteúdo completo do WIDGET_SCRIPT_CONTENT do seu código original vai aqui)
# ...
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

def gerenciar_widget_desktop(acao, config):
    """Adiciona ou remove o widget de aviso do desktop."""
    python_exe = sys.executable
    pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')

    if not os.path.exists(pythonw_exe):
        pythonw_exe = shutil.which('pythonw.exe')
        if not pythonw_exe:
            yield "ERRO CRÍTICO: pythonw.exe não foi encontrado."
            return

    if acao == 'adicionar':
        # Verifica e instala a dependência PyQt6 se necessário
        dependencia = "PyQt6"
        yield f"Verificando dependência: {dependencia}..."
        try:
            subprocess.check_call([python_exe, "-c", f"import {dependencia}"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            yield f"'{dependencia}' já está instalada."
        except subprocess.CalledProcessError:
            yield f"'{dependencia}' não encontrada. Instalando via pip..."
            processo_pip = subprocess.Popen(
                [python_exe, "-m", "pip", "install", dependencia],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                encoding='utf-8', errors='ignore', creationflags=subprocess.CREATE_NO_WINDOW
            )
            for linha in iter(processo_pip.stdout.readline, ''):
                yield f"[pip] {linha.strip()}"
            processo_pip.wait()
            if processo_pip.returncode != 0:
                yield f"ERRO: Falha ao instalar '{dependencia}'. Verifique a internet."
                return
            yield f"'{dependencia}' instalada com sucesso."

        # Criação e registro do widget
        yield f"Criando script do widget em {CAMINHO_SCRIPT_WIDGET}..."
        with open(CAMINHO_SCRIPT_WIDGET, "w", encoding="utf-8") as f:
            f.write(CONTEUDO_SCRIPT_WIDGET)

        yield "Adicionando à inicialização do Windows..."
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRO_WIDGET, 0, winreg.KEY_SET_VALUE) as key:
                comando = f'"{pythonw_exe}" "{CAMINHO_SCRIPT_WIDGET}"'
                winreg.SetValueEx(key, CHAVE_REGISTRO_WIDGET, 0, winreg.REG_SZ, comando)
            yield "Widget configurado para iniciar com o Windows."
            subprocess.Popen([pythonw_exe, CAMINHO_SCRIPT_WIDGET], creationflags=subprocess.CREATE_NO_WINDOW)
            yield "Widget adicionado com sucesso."
        except Exception as e:
            yield f"ERRO ao registrar na inicialização: {e}"

    elif acao == 'remover':
        yield "Finalizando processo do widget..."
        subprocess.run(f'taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq WidgetInfo*"', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Removendo da inicialização do Windows..."
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRO_WIDGET, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, CHAVE_REGISTRO_WIDGET)
        except FileNotFoundError:
            yield "AVISO: Registro de inicialização não encontrado."
        except Exception as e:
            yield f"ERRO ao remover do registro: {e}"

        if os.path.exists(CAMINHO_SCRIPT_WIDGET):
            os.remove(CAMINHO_SCRIPT_WIDGET)
            yield "Arquivo de script removido."
        yield "Widget removido com sucesso."


def aplicar_tema_fct(caminho_tema):
    """Aplica o tema visual da FCT."""
    yield f"Verificando tema em: {caminho_tema}"
    if not os.path.exists(caminho_tema):
        yield f"ERRO: Arquivo de tema não encontrado. Verifique o caminho nas Configurações."
        return
    try:
        os.startfile(caminho_tema)
        yield "Comando para aplicar o tema foi enviado ao Windows."
    except Exception as e:
        yield f"ERRO CRÍTICO ao tentar aplicar o tema: {e}"

def aplicar_gpos_fct(caminho_base_gpo):
    """Aplica as políticas de grupo (GPOs) da FCT."""
    lgpo_path = os.path.join(caminho_base_gpo, "lgpo.exe")
    if not os.path.exists(lgpo_path):
        yield f"ERRO: LGPO.exe não encontrado em {caminho_base_gpo}. Verifique o acesso à rede."
        return
    yield "Aplicando política de máquina..."
    subprocess.run([lgpo_path, "/t", os.path.join(caminho_base_gpo, "machine.txt")], capture_output=True)
    yield "Aplicando política de usuário..."
    subprocess.run([lgpo_path, "/t", os.path.join(caminho_base_gpo, "user.txt")], capture_output=True)
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
        subprocess.run(["wsreset.exe", "-l"], check=True, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Cache da loja limpo."
    except Exception as e:
        yield f"AVISO: Falha no wsreset.exe: {e}"

    yield "Re-registrando o aplicativo da Store..."
    comando = 'Get-AppxPackage *WindowsStore* -AllUsers | ForEach-Object {Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml"}'
    yield from executar_comando_powershell(comando)
    yield "Comando de re-registro enviado."


def habilitar_acesso_smb_legado():
    """Habilita o protocolo SMBv1 e acesso inseguro para compatibilidade."""
    yield from executar_comando_powershell('Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol-Client -NoRestart')
    yield from executar_comando_powershell('Set-SmbClientConfiguration -EnableInsecureGuestLogons $true -Force')
    yield "Configurações de SMB legado aplicadas."

def forcar_atualizacao_gpos():
    """Força a atualização das Políticas de Grupo (gpupdate)."""
    yield "Forçando atualização das Políticas de Grupo (GPOs)..."
    yield from executar_comando_powershell("gpupdate /force", timeout=120)
    yield "Tentativa de atualização de GPO concluída."