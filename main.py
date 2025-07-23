# main.py
import sys
import os
import logging
import ctypes

from PyQt6.QtWidgets import QApplication, QMessageBox
from interface_grafica import JanelaPrincipal
from backend import DIRETORIO_APP_DATA, DIRETORIO_LOGS

def configurar_ambiente():
    """Garante que os diretórios de dados e logs da aplicação existam."""
    os.makedirs(DIRETORIO_APP_DATA, exist_ok=True)
    os.makedirs(DIRETORIO_LOGS, exist_ok=True)

def configurar_logs():
    """Configura o sistema de logging para salvar em um arquivo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        filename=os.path.join(DIRETORIO_LOGS, "manutencao.log"),
        filemode='a',
        encoding="utf-8"
    )

def e_administrador():
    """Verifica se o script está sendo executado com privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def obter_stylesheet():
    """Retorna o CSS com o novo tema para estilizar a aplicação."""
    # Paleta de Cores:
    # Azul Principal: #0072B9
    # Azul Hover:     #005A9E
    # Painel Escuro:  #2C3E50
    # Fundo Claro:    #F5F5F5
    # Texto Claro:    #ECF0F1
    # Texto Escuro:   #34495E
    # Borda:          #BDC3C7
    return """
        QMainWindow, QDialog {
            background-color: #F5F5F5; /* Fundo principal (cinza muito claro) */
        }
        QWidget {
            font-family: "Segoe UI";
            color: #34495E; /* Cor de texto padrão (cinza escuro azulado) */
        }

        /* --- PAINEL ESQUERDO --- */
        #PainelEsquerdo {
            background-color: #F5F5F5; /* Fundo principal (cinza muito claro) */
        }
        #PainelEsquerdo QLabel {
            color: #34495E; /* Cor de texto padrão (cinza escuro azulado) */
            font-weight: bold;
        }

        /* --- BOTÕES --- */
        QPushButton {
            background-color: #0072B9; /* Azul principal */
            color: #FFFFFF;
            border: none;
            padding: 10px;
            text-align: left;
            font-size: 11pt;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #005A9E; /* Azul mais escuro no hover */
        }
        QPushButton:pressed {
            background-color: #004578; /* Azul ainda mais escuro ao pressionar */
        }
        QPushButton:disabled {
            background-color: #95A5A6; /* Cinza para botão desabilitado */
            color: #BDC3C7;
        }

        /* --- PAINEL DIREITO (LOG) --- */
        QTextEdit {
            background-color: #FFFFFF;
            border: 1px solid #BDC3C7; /* Borda cinza clara */
            color: #34495E;
            font-size: 10pt;
            border-radius: 4px;
        }
        QProgressBar {
            border: 1px solid #BDC3C7;
            border-radius: 4px;
            text-align: center;
            background-color: #FFFFFF;
            color: #34495E;
        }
        QProgressBar::chunk {
            background-color: #0072B9; /* Azul da barra de progresso */
            border-radius: 3px;
        }

        /* --- JANELAS DE DIÁLOGO --- */
        QLineEdit {
            background-color: #FFFFFF;
            border: 1px solid #BDC3C7;
            padding: 6px;
            border-radius: 4px;
            font-size: 10pt;
        }
        #LabelLogo {
            margin-bottom: 10px;
        }
        #LabelTituloSobre {
            font-size: 14pt;
            font-weight: bold;
            margin-bottom: 5px;
        }
        #LabelVersaoSobre {
            font-size: 10pt;
            color: #7F8C8D; /* Cinza mais claro para a versão */
            margin-bottom: 15px;
        }
    """

# --- Ponto de Entrada da Aplicação ---
if __name__ == '__main__':
    if not e_administrador():
        app_temp = QApplication(sys.argv)
        QMessageBox.critical(None, "Erro de Permissão", "Esta aplicação precisa ser executada como Administrador.")
        sys.exit(1)

    configurar_ambiente()
    configurar_logs()

    app = QApplication(sys.argv)
    app.setStyleSheet(obter_stylesheet())

    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())