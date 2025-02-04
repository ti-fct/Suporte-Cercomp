#!/usr/bin/env python
import sys
import os
import subprocess
import importlib.util
import socket
import logging

# Configuração do logging para salvar em C:\UFG\script.log
log_dir = r"C:\UFG"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "script.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def verificar_e_instalar(nome_pacote, nome_modulo=None):
    """
    Verifica se o módulo está instalado e, se não estiver,
    instala-o utilizando o pip.
    
    :param nome_pacote: Nome do pacote a ser instalado via pip.
    :param nome_modulo: Nome do módulo a ser verificado; se None, usa nome_pacote.
    """
    if nome_modulo is None:
        nome_modulo = nome_pacote

    especificacao = importlib.util.find_spec(nome_modulo)
    if especificacao is None:
        logging.info(f"Módulo '{nome_modulo}' não encontrado. Instalando '{nome_pacote}'...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", nome_pacote])
            logging.info(f"'{nome_pacote}' instalado com sucesso.")
        except subprocess.CalledProcessError as erro:
            logging.error(f"Erro ao instalar '{nome_pacote}': {erro}")
            sys.exit(1)  # Encerra o script se a instalação falhar.
    else:
        logging.info(f"Módulo '{nome_modulo}' já está instalado.")

# -----------------------------
# 1. Verificação das dependências necessárias
# -----------------------------
verificar_e_instalar("requests")
verificar_e_instalar("PyQt5")

# Agora que as dependências estão garantidas, importamos os módulos.
import requests
from PyQt5 import QtWidgets, QtCore, QtGui

# -----------------------------
# 2. Função de Auto-Update
# -----------------------------
def atualizar_script():
    url = "https://raw.githubusercontent.com/ti-fct/scripts/refs/heads/main/avisoLabs.py"
    
    try:
        resposta = requests.get(url)
        resposta.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Erro ao acessar a URL para atualização: {e}")
        return

    conteudo_remoto = resposta.text
    caminho_script = os.path.realpath(__file__)

    try:
        with open(caminho_script, "r", encoding="utf-8") as arquivo:
            conteudo_atual = arquivo.read()
    except Exception as e:
        logging.error(f"Erro ao ler o script atual: {e}")
        return

    # Normaliza quebras de linha para LF
    conteudo_remoto_normalizado = re.sub(r'\r\n?', '\n', conteudo_remoto)
    conteudo_atual_normalizado = re.sub(r'\r\n?', '\n', conteudo_atual)

    if conteudo_atual_normalizado != conteudo_remoto_normalizado:
        logging.info("Nova versão encontrada. Atualizando o script...")
        try:
            # Escreve com newline='\n' para manter LF
            with open(caminho_script, "w", encoding="utf-8", newline='\n') as arquivo:
                arquivo.write(conteudo_remoto)
            logging.info("Script atualizado com sucesso. Reinicie o programa.")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Erro ao atualizar: {e}")
            sys.exit(1)
    else:
        logging.info("Script já está atualizado.")

# Executa o autoupdate somente após a verificação das dependências.
atualizar_script()

# -----------------------------
# 3. Código Principal (Interface gráfica com PyQt5)
# -----------------------------
class WidgetInfo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.configurar_interface()

    def configurar_interface(self):
        # Define a janela sem bordas, transparente e que fique abaixo de outras janelas.
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint |
                            QtCore.Qt.WindowStaysOnBottomHint |
                            QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Cria o rótulo com o texto (alinhado à direita).
        self.rotulo = QtWidgets.QLabel(self)
        self.rotulo.setText(self.formatar_texto())
        self.rotulo.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.rotulo.setStyleSheet("QLabel { color: white; font-size: 11pt; }")

        # Adiciona um efeito de sombra preta no texto.
        sombra = QtWidgets.QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(5)
        sombra.setOffset(2, 2)
        sombra.setColor(QtGui.QColor(0, 0, 0))
        self.rotulo.setGraphicsEffect(sombra)

        # Layout para posicionar o rótulo com margens.
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.rotulo)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        # Ajusta o tamanho da janela de acordo com o conteúdo.
        self.adjustSize()
        # Posiciona a janela no canto superior direito com uma margem.
        self.posicionar_widget()

    def formatar_texto(self):
        # Obtém informações do sistema: nome do computador e IP local.
        nome_computador = socket.gethostname()
        ip_local = socket.gethostbyname(socket.gethostname())
        # Formata o texto com emojis e separadores.
        texto = (
            "<p style='margin:0; text-align:right; color:white;'>"
            "<b>💻 LAB. DE INFORMÁTICA - FCT/UFG</b><br>"
            "───────────────────────────<br>"
            f"{nome_computador}<br><br>"
#            f"{ip_local}<br><br>"
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
            "💬 (62)3209-6555"
            "</p>"
        )
        return texto   

    def posicionar_widget(self):
        # Recupera a geometria da área de trabalho principal.
        tela = QtWidgets.QApplication.primaryScreen()
        retangulo_disponivel = tela.availableGeometry()
        largura_widget = self.width()
        altura_widget = self.height()
        margem = 20  # margem em pixels
        # Posiciona no canto superior direito.
        x = retangulo_disponivel.right() - largura_widget - margem
        y = retangulo_disponivel.top() + margem
        self.move(x, y)

    def changeEvent(self, evento):
        # Impede que a janela seja minimizada: se ocorrer minimização, restaura imediatamente.
        if evento.type() == QtCore.QEvent.WindowStateChange:
            if self.windowState() & QtCore.Qt.WindowMinimized:
                QtCore.QTimer.singleShot(0, self.showNormal)
        super().changeEvent(evento)

def principal():
    logging.info("Iniciando aplicação...")
    app = QtWidgets.QApplication(sys.argv)
    widget = WidgetInfo()
    widget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    principal()
