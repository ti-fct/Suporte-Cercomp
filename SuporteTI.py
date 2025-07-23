# ManutencaoUFG_GUI_v5.py
import sys
import os
import subprocess
import logging
import ctypes
import shutil
import json
import time
import socket
import winreg
import requests
import zipfile

# --- Dependências da GUI ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QProgressBar, QMessageBox, QInputDialog,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, Qt, QEvent, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor
import qtawesome as qta

# --- CONFIGURAÇÃO CENTRALIZADA (sem alterações) ---
APP_DATA_DIR = r"C:\ProgramData\ManutencaoUFG"
LOG_DIRECTORY = os.path.join(APP_DATA_DIR, "logs")
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")
WIDGET_SCRIPT_PATH = os.path.join(APP_DATA_DIR, "AvisoDesktop.pyw")
WIDGET_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
WIDGET_REG_KEY_NAME = "FCT_UFG_DesktopInfo"

# --- Conteúdo do script do widget (sem alterações) ---
WIDGET_SCRIPT_CONTENT = """
# (O mesmo conteúdo do WIDGET_SCRIPT_CONTENT da versão anterior)
# ...
import sys
import socket
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
    from PyQt6.QtCore import Qt, QEvent, QTimer
    from PyQt6.QtGui import QColor
except ImportError:
    # Se a importação falhar, o script não deve travar, apenas sair silenciosamente.
    # A ferramenta principal é responsável por instalar as dependências.
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

# --- Classe ConfigManager e SettingsDialog (sem alterações) ---
# ...
class ConfigManager:
    def __init__(self, filepath=CONFIG_FILE):
        self.filepath = filepath
        self.defaults = {
            "THEME_PATH": r"\\fog\gpos\fct-labs.deskthemepack",
            "GPO_BASE_PATH": r"\\fog\gpos",
            "BLEACHBIT_URL": "https://download.bleachbit.org/BleachBit-4.6.0-portable.zip",
            "BLEACHBIT_CLEANERS": "system.temp,system.recycle_bin,deep_scan.temp"
        }
    def load_config(self):
        if not os.path.exists(self.filepath): self.save_config(self.defaults)
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f: config = json.load(f)
            for key, value in self.defaults.items(): config.setdefault(key, value)
            return config
        except (json.JSONDecodeError, IOError):
            self.save_config(self.defaults)
            return self.defaults
    def save_config(self, data):
        with open(self.filepath, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config_data = self.config_manager.load_config()
        self.setWindowTitle("Configurações"); self.setMinimumWidth(500)
        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.inputs = {}
        for key, value in self.config_data.items():
            line_edit = QLineEdit(value)
            form_layout.addRow(QLabel(key.replace("_", " ").title() + ":"), line_edit)
            self.inputs[key] = line_edit
        self.layout.addLayout(form_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_and_accept); button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)
    def save_and_accept(self):
        for key, line_edit in self.inputs.items(): self.config_data[key] = line_edit.text()
        self.config_manager.save_config(self.config_data)
        self.accept()

# --- LÓGICA DE BACKEND ---

# ALTERADO: A lógica do widget agora inclui a instalação de dependências.
def manage_desktop_widget_logic(action):
    """Adiciona ou remove o widget de aviso do desktop, garantindo as dependências."""
    
    # Encontra o executável python.exe para usar com o pip.
    python_exe_path = sys.executable
    # Encontra o pythonw.exe para executar o script em segundo plano.
    pythonw_path = python_exe_path.replace('python.exe', 'pythonw.exe')
    
    if not os.path.exists(pythonw_path):
        pythonw_path = shutil.which('pythonw.exe')
        if not pythonw_path:
            yield "ERRO CRÍTICO: pythonw.exe não encontrado no sistema. Não é possível gerenciar o widget."
            return

    if action == 'add':
        # --- NOVO: Etapa de verificação e instalação de dependências ---
        dependency = "PyQt6"
        yield f"Verificando a dependência: {dependency}..."
        
        # Comando para verificar se o módulo está instalado, sem gerar erros.
        check_command = [python_exe_path, "-c", f"import {dependency}"]
        
        # Usamos subprocess.run para esperar o resultado.
        result = subprocess.run(check_command, capture_output=True, text=True)
        
        if result.returncode != 0:
            yield f"Dependência '{dependency}' não encontrada. Tentando instalar..."
            
            # Comando para instalar o pacote usando pip.
            install_command = [python_exe_path, "-m", "pip", "install", dependency]
            
            # Executa a instalação e mostra o progresso no console.
            install_process = subprocess.Popen(
                install_command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                encoding='utf-8', 
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Transmite a saída do pip para o log da GUI.
            for line in iter(install_process.stdout.readline, ''):
                yield f"[pip] {line.strip()}"
            
            install_process.wait() # Espera o processo terminar.
            
            if install_process.returncode == 0:
                yield f"Dependência '{dependency}' instalada com sucesso."
            else:
                error_output = install_process.stderr.read()
                yield f"ERRO: Falha ao instalar '{dependency}'. Verifique a conexão com a internet ou o log abaixo."
                yield f"[pip-error] {error_output.strip()}"
                return # Interrompe a execução se a instalação falhar.
        else:
            yield f"Dependência '{dependency}' já está instalada."
        
        # --- Continuação da lógica anterior ---
        yield f"Criando script do widget em {WIDGET_SCRIPT_PATH}..."
        with open(WIDGET_SCRIPT_PATH, "w", encoding="utf-8") as f:
            f.write(WIDGET_SCRIPT_CONTENT)
        yield "Script salvo com sucesso."

        yield "Adicionando à inicialização do Windows..."
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIDGET_REG_PATH, 0, winreg.KEY_SET_VALUE)
            command_to_run = f'"{pythonw_path}" "{WIDGET_SCRIPT_PATH}"'
            winreg.SetValueEx(key, WIDGET_REG_KEY_NAME, 0, winreg.REG_SZ, command_to_run)
            winreg.CloseKey(key)
            yield "Registro de inicialização criado com sucesso."
        except Exception as e:
            yield f"ERRO ao escrever no registro: {e}"
            return

        yield "Iniciando o widget na sessão atual..."
        subprocess.Popen([pythonw_path, WIDGET_SCRIPT_PATH], creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Widget de aviso adicionado ao desktop."

    elif action == 'remove':
        # Lógica de remoção (sem alterações)
        yield "Finalizando processo do widget (se estiver em execução)..."
        subprocess.run(f'taskkill /F /IM pythonw.exe', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Processo do widget finalizado."
        yield "Removendo da inicialização do Windows..."
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIDGET_REG_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, WIDGET_REG_KEY_NAME)
            winreg.CloseKey(key)
        except FileNotFoundError:
            yield "AVISO: Registro de inicialização não encontrado."
        except Exception as e:
            yield f"ERRO ao remover do registro: {e}"
        yield "Removendo arquivo de script..."
        if os.path.exists(WIDGET_SCRIPT_PATH):
            os.remove(WIDGET_SCRIPT_PATH)
            yield "Arquivo de script removido."
        yield "Widget de aviso removido com sucesso."

def apply_theme_logic(theme_path):
    yield f"Verificando o caminho do tema: {theme_path}"
    if not os.path.exists(theme_path):
        yield f"ERRO: Arquivo de tema não encontrado. Verifique a conexão com a rede e o caminho nas Configurações."
        return
    try:
        yield "Arquivo de tema encontrado. Aplicando..."
        os.startfile(theme_path)
        yield "Comando para aplicar o tema foi enviado ao Windows."
    except Exception as e:
        yield f"ERRO CRÍTICO ao tentar aplicar o tema: {e}"
def apply_fct_gpos_logic(gpo_base_path):
    lgpo_path = os.path.join(gpo_base_path, "lgpo.exe")
    if not os.path.exists(lgpo_path):
        yield f"ERRO: LGPO.exe não encontrado em {gpo_base_path}. Verifique o acesso à rede e o caminho nas Configurações."
        return
    yield "Aplicando política de máquina..."
    subprocess.run([lgpo_path, "/t", os.path.join(gpo_base_path, "machine.txt")], capture_output=True)
    yield "Aplicando política de usuário..."
    subprocess.run([lgpo_path, "/t", os.path.join(gpo_base_path, "user.txt")], capture_output=True)
    yield "GPOs aplicadas com sucesso."
def start_system_cleanup_logic(tool_url, cleaners):
    temp_dir = os.environ.get("TEMP", r"C:\Windows\Temp")
    tool_dir = os.path.join(temp_dir, "BleachBit")
    zip_path = os.path.join(temp_dir, "BleachBit.zip")
    try:
        yield f"Baixando BleachBit de {tool_url}..."
        response = requests.get(tool_url, stream=True)
        response.raise_for_status()
        with open(zip_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        yield f"Extraindo para {tool_dir}..."
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tool_dir)
        bleachbit_console = os.path.join(tool_dir, "bleachbit_console.exe")
        yield f"Executando limpeza com BleachBit (limpadores: {cleaners}). Isso pode demorar..."
        subprocess.run([bleachbit_console, "-c", cleaners], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Limpeza concluída!"
    except Exception as e:
        yield f"ERRO durante a limpeza: {e}"
    finally:
        if os.path.exists(tool_dir): shutil.rmtree(tool_dir, ignore_errors=True)
        if os.path.exists(zip_path): os.remove(zip_path)
def run_powershell_command(command, timeout=180):
    """
    Executa um comando PowerShell com um timeout.

    Args:
        command (str): O comando a ser executado.
        timeout (int): Tempo máximo de espera em segundos. Padrão é 180 (3 minutos).

    Yields:
        str: A saída do comando ou mensagens de erro/status.
    """
    yield f"Executando comando (timeout: {timeout}s): {command[:70]}..."
    try:
        # Trocamos Popen por run para usar o parâmetro 'timeout' de forma simples e segura.
        process = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=timeout, # <- O parâmetro chave para o timeout!
            check=False      # Não levanta exceção para códigos de retorno != 0
        )

        # Retorna a saída padrão se houver alguma.
        if process.stdout:
            yield process.stdout.strip()

        # Verifica o código de retorno após a execução.
        if process.returncode != 0:
            yield f"ERRO: O comando PowerShell retornou o código {process.returncode}."
            if process.stderr:
                yield f"Detalhes do erro: {process.stderr.strip()}"

    except subprocess.TimeoutExpired:
        # Captura a exceção específica de timeout.
        yield f"ERRO: O comando excedeu o tempo limite de {timeout} segundos e foi interrompido."
    except Exception as e:
        yield f"ERRO CRÍTICO ao executar PowerShell: {e}"
def set_computer_name_logic(new_name):
    yield f"Tentando alterar o nome para '{new_name}'..."
    yield from run_powershell_command(f'Rename-Computer -NewName "{new_name}" -Force -ErrorAction Stop')
    yield "Nome alterado! É necessário reiniciar para aplicar."
def restore_default_gpos_logic():
    gpo_paths = [
        os.path.join(os.environ['WINDIR'], 'System32', 'GroupPolicy'),
        os.path.join(os.environ['WINDIR'], 'System32', 'GroupPolicyUsers')
    ]
    for path in gpo_paths:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                yield f"Removido: {path}"
            except Exception as e:
                yield f"ERRO ao remover {path}: {e}"
        # Passamos um timeout de 120 segundos (2 minutos) para o gpupdate.
    yield from run_powershell_command("gpupdate /force", timeout=120)
    yield "Restauração das GPOs padrão concluída."
def reset_windows_store_logic():
    yield "Iniciando reset da Microsoft Store..."
    try:
        subprocess.run(["wsreset.exe"], check=True, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Cache da loja limpo."
    except Exception as e:
        yield f"AVISO: Falha no wsreset.exe: {e}"
    yield "Re-registrando o aplicativo da Store..."
    command = 'Get-AppxPackage *WindowsStore* -AllUsers | ForEach-Object {Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml"}'
    yield from run_powershell_command(command)
    yield "Comando de re-registro enviado."
def enable_smb_legacy_access_logic():
    yield from run_powershell_command('Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol-Client -NoRestart')
    yield from run_powershell_command('Set-SmbClientConfiguration -EnableInsecureGuestLogons $true -Force')
    yield "Configurações de SMB legado aplicadas."
def update_group_policies_logic():
    yield "Forçando atualização das Políticas de Grupo (GPOs)..."
    yield from run_powershell_command("gpupdate /force", timeout=120)
    yield "Tentativa de atualização de GPO concluída."

# --- WORKER DE THREAD (sem alterações) ---
class Worker(QObject):
    # ... (código da v3 sem alterações) ...
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
    def run(self):
        try:
            generator = self.function(*self.args, **self.kwargs)
            for result in generator:
                if result: self.progress.emit(str(result)); time.sleep(0.05)
        except Exception as e:
            self.progress.emit(f"ERRO NÃO TRATADO NA TAREFA: {e}")
        finally:
            self.finished.emit()

# --- INTERFACE GRÁFICA PRINCIPAL (sem alterações de layout) ---
class MainWindow(QMainWindow):
    # ... (código da v3, mas agora ele usa as constantes centralizadas) ...
    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None
        self.config_manager = ConfigManager() # Usa o caminho global CONFIG_FILE
        self.config = self.config_manager.load_config()
        self.initUI()
        self.log_to_console("Ferramenta de Manutenção FCT/UFG v4.0 pronta.")
        self.log_to_console(f"Arquivos centralizados em: {APP_DATA_DIR}")
        self.log_to_console("Selecione uma ação no menu à esquerda.")

    def initUI(self):
        self.setWindowTitle("Ferramenta de Manutenção FCT/UFG v4.0")
        #... O resto da UI é idêntico ao da v3
        self.setWindowIcon(qta.icon('fa5s.tools', color='white'))
        self.setGeometry(100, 100, 1000, 600)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        title_label = QLabel("Ações Rápidas")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(title_label)
        buttons_to_create = [
            ("Renomear Computador", 'fa5s.laptop-code', self.run_set_computer_name),
            ("Aplicar GPOs FCT", 'fa5s.university', lambda: self.run_task(apply_fct_gpos_logic, self.config['GPO_BASE_PATH'])),
            ("Aplicar Tema FCT", 'fa5s.palette', lambda: self.run_task(apply_theme_logic, self.config['THEME_PATH'])),
            ("Restaurar GPOs Padrão", 'fa5s.undo-alt', lambda: self.run_task_with_confirmation(restore_default_gpos_logic, "Restaurar GPOs?", "Isso removerá todas as políticas locais. Tem certeza?")),
            ("Forçar Atualizar GPOs", 'fa5s.sync-alt', lambda: self.run_task(update_group_policies_logic)),
            ("Resetar Microsoft Store", 'fa5s.store-alt', lambda: self.run_task(reset_windows_store_logic)),
            ("Habilitar SMBv1 (Win11)", 'fa5s.folder-open', lambda: self.run_task_with_confirmation(enable_smb_legacy_access_logic, "Habilitar SMBv1?", "Isso habilita um protocolo inseguro. Use apenas em redes confiáveis.")),
            ("Limpeza Geral", 'fa5s.broom', lambda: self.run_task(start_system_cleanup_logic, self.config['BLEACHBIT_URL'], self.config['BLEACHBIT_CLEANERS'])),
        ]
        self.action_buttons = []
        for text, icon_name, func in buttons_to_create:
            btn = QPushButton(f" {text}")
            btn.setIcon(qta.icon(icon_name, color='white'))
            btn.clicked.connect(func)
            left_panel.addWidget(btn)
            self.action_buttons.append(btn)
        left_panel.addSpacing(20)
        widget_title_label = QLabel("Aviso de Desktop")
        widget_title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        widget_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(widget_title_label)
        add_widget_btn = QPushButton(" Adicionar Aviso ao Desktop")
        add_widget_btn.setIcon(qta.icon('fa5s.plus-circle', color='white'))
        add_widget_btn.clicked.connect(lambda: self.run_task(manage_desktop_widget_logic, 'add'))
        left_panel.addWidget(add_widget_btn)
        self.action_buttons.append(add_widget_btn)
        remove_widget_btn = QPushButton(" Remover Aviso do Desktop")
        remove_widget_btn.setIcon(qta.icon('fa5s.minus-circle', color='white'))
        remove_widget_btn.clicked.connect(lambda: self.run_task_with_confirmation(lambda: manage_desktop_widget_logic('remove'), "Remover Aviso?", "Isso irá finalizar o aviso e removê-lo da inicialização. Tem certeza?"))
        left_panel.addWidget(remove_widget_btn)
        self.action_buttons.append(remove_widget_btn)
        left_panel.addStretch()
        settings_btn = QPushButton(" Configurações")
        settings_btn.setIcon(qta.icon('fa5s.cog', color='white'))
        settings_btn.clicked.connect(self.open_settings_dialog)
        left_panel.addWidget(settings_btn)
        self.action_buttons.append(settings_btn)
        right_panel = QVBoxLayout()
        log_label = QLabel("Console de Log")
        log_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        log_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setFont(QFont("Consolas", 10))
        right_panel.addWidget(log_label)
        right_panel.addWidget(self.log_console)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        right_panel.addWidget(self.progress_bar)
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 3)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.log_to_console("\n⚙️ Configurações salvas e recarregadas.")
            self.config = self.config_manager.load_config()
        else:
            self.log_to_console("\n❌ Alteração de configurações cancelada.")
    def log_to_console(self, message):
        self.log_console.append(message)
        logging.info(message)
        self.log_console.verticalScrollBar().setValue(self.log_console.verticalScrollBar().maximum())
    def set_ui_enabled(self, enabled):
        for btn in self.action_buttons: btn.setEnabled(enabled)
    def on_task_finished(self):
        self.log_to_console("\n✅ Tarefa concluída.")
        self.progress_bar.setVisible(False)
        self.set_ui_enabled(True)
    def run_task(self, task_function, *args):
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.log_console.clear()
        task_name = task_function.__name__.replace('_logic', '').replace('_', ' ').title()
        self.log_to_console(f"🚀 Iniciando tarefa: {task_name}...")
        self.thread = QThread()
        self.worker = Worker(task_function, *args)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.log_to_console)
        self.thread.finished.connect(self.on_task_finished)
        self.thread.start()
    def run_task_with_confirmation(self, task_function, title, text, *args):
        reply = QMessageBox.question(self, title, text, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.run_task(lambda: task_function(*args))
    def run_set_computer_name(self):
        current_name = socket.gethostname()
        new_name, ok = QInputDialog.getText(self, "Alterar Nome do Computador", f"Nome atual: {current_name}\n\nDigite o novo nome:", text=current_name)
        if ok and new_name and new_name != current_name:
            if 1 <= len(new_name) <= 15 and new_name.replace('-', '').isalnum():
                 self.run_task(set_computer_name_logic, new_name)
            else:
                QMessageBox.warning(self, "Nome Inválido", "O nome deve ter entre 1 e 15 caracteres alfanuméricos (com hífens).")

# --- FUNÇÕES DE SETUP E EXECUÇÃO ---
# NOVO: Função para criar a pasta centralizada
def setup_environment():
    """Garante que o diretório de dados do aplicativo exista."""
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIRECTORY, exist_ok=True)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        filename=os.path.join(LOG_DIRECTORY, "manutencao.log"), # Usa o caminho centralizado
        filemode='a',
        encoding="utf-8"
    )

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

# --- PONTO DE ENTRADA ---
if __name__ == '__main__':
    if not is_admin():
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "Erro de Permissão", "Esta aplicação precisa ser executada como Administrador.")
        sys.exit(1)

    # ALTERADO: A configuração do ambiente é o primeiro passo
    setup_environment() 
    setup_logging()

    app = QApplication(sys.argv)
    
    # CSS (sem alterações)
    app.setStyleSheet("""
    ...
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())