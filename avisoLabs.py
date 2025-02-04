import sys
import socket
from PyQt5 import QtWidgets, QtCore, QtGui

class InfoWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self):
        # Define a janela sem bordas, transparente e que fique abaixo de outras janelas
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint |
                            QtCore.Qt.WindowStaysOnBottomHint |
                            QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Cria o label com o texto (texto alinhado à direita)
        self.label = QtWidgets.QLabel(self)
        self.label.setText(self.formatText())
        self.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.label.setStyleSheet("QLabel { color: white; font-size: 11pt; }")

        # Adiciona um efeito de sombra preta no texto
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(5)
        shadow.setOffset(2, 2)
        shadow.setColor(QtGui.QColor(0, 0, 0))
        self.label.setGraphicsEffect(shadow)

        # Layout para posicionar o label com margens
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        # Ajusta o tamanho da janela de acordo com o conteúdo
        self.adjustSize()

        # Posiciona a janela no canto superior direito com uma margem
        self.positionWidget()

    def formatText(self):
        # Obtém informações do sistema: nome do computador e IP local
        hostname = socket.gethostname()

        # Formata o texto com emojis e separadores; ajuste os ícones conforme o contexto de cada mensagem
        texto = (
            "<p style='margin:0; text-align:right; color:white;'>"
            "<b>💻 LAB. DE INFORMÁTICA - FCT/UFG</b><br>"
            "────────────────────────────<br>"
            ""+ hostname +"<br><br>"
            "<b>📜 REGRAS DE USO</b><br>"
            "🎓 Uso exclusivo para atividades acadêmicas<br>"
            "🚫 Não consumir alimentos no laboratório<br>"
            "⚙️ Não alterar configurações do sistema<br><br>"
            "<b>🚪 PROCEDIMENTOS AO SAIR</b><br>"
            "💾 Remova dispositivos externos<br>"
            "❌ Encerre todos os aplicativos<br>"
            "🔒 Faça logout das contas<br><br>"
            "<b>🛠️ SUPORTE TÉCNICO</b><br>"
            "🌐chamado.ufg.br<br>"
            "💬(62)3209-6555"
            "</p>"
        )
        return texto   

    def positionWidget(self):
        # Recupera a geometria da área de trabalho principal
        screen = QtWidgets.QApplication.primaryScreen()
        available_rect = screen.availableGeometry()
        widget_width = self.width()
        widget_height = self.height()
        margin = 20  # margem em pixels
        # Posiciona no canto superior direito
        x = available_rect.right() - widget_width - margin
        y = available_rect.top() + margin
        self.move(x, y)

    def changeEvent(self, event):
        # Impede que a janela seja minimizada: se ocorrer minimização, restaura imediatamente
        if event.type() == QtCore.QEvent.WindowStateChange:
            if self.windowState() & QtCore.Qt.WindowMinimized:
                QtCore.QTimer.singleShot(0, self.showNormal)
        super().changeEvent(event)

def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = InfoWidget()
    widget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
