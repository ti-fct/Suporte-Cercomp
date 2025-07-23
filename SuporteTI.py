import os
import sys
import subprocess
import logging
import ctypes
import shutil
import requests
import zipfile
import socket
from PyQt5 import QtWidgets, QtCore, QtGui

# --- CONFIGURAÇÃO INICIAL ---

LOG_DIRECTORY = r"C:\UFG_Manutencao"
LOG_FILE = os.path.join(LOG_DIRECTORY, "script.log")

def setup_logging():
    """Configura o sistema de log para arquivo e console."""
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def is_admin():
    """Verifica se o script está rodando com privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_powershell_command(command):
    """Executa um comando PowerShell e retorna o resultado."""
    logging.info(f"Executando comando PowerShell: {command}")
    try:
        # Usa -NoProfile e -ExecutionPolicy Bypass para garantir a execução
        completed_process = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            check=True,  # Lança uma exceção se o comando retornar um código de erro
            encoding='cp850', # Codificação comum para o console do Windows
        )
        if completed_process.stdout:
            logging.info(f"Saída: {completed_process.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() or e.stdout.strip()
        logging.error(f"Erro ao executar PowerShell: {error_message}")
        return False
    except FileNotFoundError:
        logging.error("Erro: 'powershell.exe' não encontrado. Verifique se o PowerShell está no PATH do sistema.")
        return False


# --- FUNÇÕES DO MENU ---

def set_computer_name():
    logging.info("Iniciando 'Alterar Nome do Computador'.")
    current_name = socket.gethostname()
    logging.info(f"Nome atual: {current_name}")
    
    new_name = input("Digite o novo nome (máx. 15 caracteres alfanuméricos): ").strip()
    if not (1 <= len(new_name) <= 15 and new_name.isalnum()):
        logging.error("Nome inválido.")
        return

    confirm = input(f"Confirmar alteração para '{new_name}'? (s/n): ").lower()
    if confirm == 's':
        command = f'Rename-Computer -NewName "{new_name}" -Force -ErrorAction Stop'
        if run_powershell_command(command):
            logging.info("Nome alterado com sucesso! É necessário reiniciar.")
            reboot = input("Reiniciar agora? (s/n): ").lower()
            if reboot == 's':
                subprocess.run(["shutdown", "/r", "/t", "15"])
    else:
        logging.info("Operação cancelada.")

def apply_fct_gpos():
    logging.info("Iniciando 'Aplicar GPOs da FCT'.")
    gpo_base_path = r"\\fog\gpos"
    lgpo_path = os.path.join(gpo_base_path, "lgpo.exe")
    user_policy = os.path.join(gpo_base_path, "user.txt")
    machine_policy = os.path.join(gpo_base_path, "machine.txt")

    if not os.path.exists(lgpo_path):
        logging.error(f"LGPO.exe não encontrado em {gpo_base_path}. Verifique o acesso à rede.")
        return

    try:
        logging.info("Aplicando política de máquina...")
        subprocess.run([lgpo_path, "/t", machine_policy], check=True)
        logging.info("Aplicando política de usuário...")
        subprocess.run([lgpo_path, "/t", user_policy], check=True)
        logging.info("GPOs aplicadas com sucesso.")
    except Exception as e:
        logging.error(f"Falha ao aplicar GPOs: {e}")

def restore_default_gpos():
    logging.info("Iniciando 'Restaurar GPOs Padrão'.")
    confirm = input("ATENÇÃO: Isso removerá TODAS as políticas de grupo locais. Continuar? (s/n): ").lower()
    if confirm != 's':
        logging.info("Operação cancelada.")
        return

    gpo_paths = [
        os.path.join(os.environ['WINDIR'], 'System32', 'GroupPolicy'),
        os.path.join(os.environ['WINDIR'], 'System32', 'GroupPolicyUsers')
    ]
    for path in gpo_paths:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                logging.info(f"Removido: {path}")
            except Exception as e:
                logging.error(f"Erro ao remover {path}: {e}")
    
    logging.info("Restaurado com sucesso. Forçando atualização das políticas...")
    subprocess.run(["gpupdate", "/force"])

def update_group_policies():
    logging.info("Forçando atualização das políticas de grupo...")
    subprocess.run(["gpupdate", "/force"])
    logging.info("Comando de atualização enviado.")

def reset_windows_store():
    logging.info("Iniciando 'Resetar Microsoft Store'.")
    command = 'Get-AppxPackage *WindowsStore* | Reset-AppxPackage'
    if run_powershell_command(command):
        logging.info("Comando para resetar a Store enviado com sucesso.")
    else:
        logging.error("Falha ao executar o comando de reset da Store.")
        
def enable_smb_legacy_access():
    logging.warning("Habilitando acesso legado SMBv1. Use apenas em redes confiáveis.")
    # Habilita o protocolo SMBv1 (cliente)
    command_smb1 = 'Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol-Client -NoRestart'
    logging.info("Tentando habilitar o protocolo SMBv1...")
    run_powershell_command(command_smb1)

    # Habilita logon de convidado inseguro
    command_guest = 'Set-SmbClientConfiguration -EnableInsecureGuestLogons $true -Force'
    logging.info("Tentando habilitar logon de convidado inseguro...")
    run_powershell_command(command_guest)
    logging.info("Configurações de SMB legado aplicadas. Pode ser necessário reiniciar.")

def start_system_cleanup():
    logging.info("Iniciando 'Limpeza Geral do Sistema'.")
    temp_dir = os.environ.get("TEMP", r"C:\Windows\Temp")
    tool_dir = os.path.join(temp_dir, "BleachBit")
    zip_path = os.path.join(temp_dir, "BleachBit.zip")
    tool_url = "https://download.bleachbit.org/BleachBit-4.6.0-portable.zip"
    
    try:
        # Download e extração
        logging.info(f"Baixando BleachBit de {tool_url}...")
        response = requests.get(tool_url)
        response.raise_for_status()
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        logging.info(f"Extraindo para {tool_dir}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tool_dir)
        
        # Execução
        bleachbit_console = os.path.join(tool_dir, "bleachbit_console.exe")
        cleaners = "system.temp,system.recycle_bin,deep_scan.temp"
        logging.info("Executando limpeza automatizada com BleachBit...")
        subprocess.run([bleachbit_console, "-c", cleaners], check=True)
        
        logging.info("Limpando pastas de usuário...")
        for user_profile in os.scandir("C:\\Users"):
            if user_profile.is_dir() and user_profile.name not in ["Public", "Default", "All Users"]:
                # Limpar Downloads
                downloads_path = os.path.join(user_profile.path, "Downloads")
                if os.path.exists(downloads_path):
                    shutil.rmtree(downloads_path, ignore_errors=True)
                    os.makedirs(downloads_path) # Recria a pasta vazia
                # Limpar Desktop (mantendo atalhos .lnk)
                desktop_path = os.path.join(user_profile.path, "Desktop")
                if os.path.exists(desktop_path):
                    for item in os.listdir(desktop_path):
                        item_path = os.path.join(desktop_path, item)
                        if not item.lower().endswith('.lnk'):
                            if os.path.isfile(item_path) or os.path.islink(item_path):
                                os.remove(item_path)
                            elif os.path.isdir(item_path):
                                shutil.rmtree(item_path)

        logging.info("Limpeza geral concluída com sucesso!")
        
    except Exception as e:
        logging.error(f"Erro durante a limpeza: {e}")
    finally:
        # Limpeza da ferramenta
        if os.path.exists(tool_dir): shutil.rmtree(tool_dir, ignore_errors=True)
        if os.path.exists(zip_path): os.remove(zip_path)

def configure_desktop_warning():
    """Função para configurar e exibir o widget de aviso."""
    logging.info("Configurando o aviso fixo no Desktop.")
    # O código do widget PyQt5 vai aqui.
    # Esta é uma implementação simplificada para demonstração.
    try:
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        
        class InfoWidget(QtWidgets.QWidget):
            def __init__(self):
                super().__init__()
                self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnBottomHint | QtCore.Qt.Tool)
                self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
                
                layout = QtWidgets.QVBoxLayout(self)
                self.label = QtWidgets.QLabel(self.get_display_text())
                self.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
                self.label.setStyleSheet("QLabel { color: white; font-size: 11pt; }")
                
                shadow = QtWidgets.QGraphicsDropShadowEffect(self)
                shadow.setBlurRadius(5)
                shadow.setOffset(2, 2)
                shadow.setColor(QtGui.QColor(0, 0, 0))
                self.label.setGraphicsEffect(shadow)
                
                layout.addWidget(self.label)
                self.setLayout(layout)
                
                self.adjustSize()
                self.position_widget()

            def get_display_text(self):
                hostname = socket.gethostname()
                return (
                    f"<p style='text-align:right;'>"
                    f"<b>💻 LAB. DE INFORMÁTICA - FCT/UFG</b><br>"
                    f"───────────────────────────<br>"
                    f"{hostname}<br><br>"
                    f"<b>📜 REGRAS DE USO</b><br>"
                    f"🎓 Uso exclusivo para atividades acadêmicas<br>"
                    f"🚫 Não consumir alimentos no laboratório<br>"
                    f"⚙️ Não alterar configurações do sistema<br><br>"
                    f"<b>🛠️ SUPORTE TÉCNICO</b><br>"
                    f"🌐 chamado.ufg.br<br>"
                    f"💬 (62) 3209-6555"
                    f"</p>"
                )

            def position_widget(self):
                screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
                self.move(screen_geometry.right() - self.width() - 20, screen_geometry.top() + 20)

        # Para que o widget não morra, precisamos mantê-lo em uma variável global ou similar
        # no contexto de um menu, é melhor apenas lançá-lo como um processo separado.
        # Por simplicidade aqui, apenas mostraremos. O ideal seria salvar um script e adicioná-lo à inicialização.
        global info_widget 
        info_widget = InfoWidget()
        info_widget.show()
        logging.info("Widget de aviso exibido. Feche-o manualmente se necessário.")
        # Em um app real, app.exec_() iniciaria o loop de eventos.
        
    except Exception as e:
        logging.error(f"Não foi possível iniciar o widget de aviso: {e}")
        logging.error("Verifique se as dependências (PyQt5) estão instaladas.")


# --- MENU PRINCIPAL ---

def main_menu():
    menu_options = {
        '1': ('Alterar Nome do Computador', set_computer_name),
        '2': ('Aplicar GPOs da FCT', apply_fct_gpos),
        '3': ('Restaurar GPOs Padrão do Windows', restore_default_gpos),
        '4': ('Atualizar GPOs', update_group_policies),
        '5': ('Resetar Microsoft Store', reset_windows_store),
        '6': ('Habilitar Acesso a Pastas de Rede Legadas (SMBv1)', enable_smb_legacy_access),
        '7': ('Limpeza Geral do Sistema (com BleachBit)', start_system_cleanup),
        '8': ('Adicionar Aviso Fixo no Desktop', configure_desktop_warning),
        '9': ('Sair', sys.exit)
    }

    while True:
        print("\n" + "="*50)
        print("    Ferramenta de Manutenção FCT/UFG (Python Edition)")
        print("="*50)
        for key, value in menu_options.items():
            print(f" {key}. {value[0]}")
        print("="*50)
        
        choice = input("Selecione uma opção: ").strip()
        
        if choice in menu_options:
            if choice == '9':
                logging.info("Saindo do script.")
                menu_options[choice][1]()
            else:
                menu_options[choice][1]()
                input("\nPressione Enter para continuar...")
        else:
            print("Opção inválida!")


if __name__ == "__main__":
    setup_logging()
    
    if not is_admin():
        logging.error("Acesso negado. Este script precisa ser executado como Administrador.")
        # Re-executa o script com privilégios de administrador
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        except Exception as e:
            logging.error(f"Falha ao tentar elevação automática: {e}")
            input("Pressione Enter para sair.")
    else:
        logging.info("="*10 + " SCRIPT DE MANUTENÇÃO INICIADO (ADMIN) " + "="*10)
        main_menu()