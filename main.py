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
    # Azul Principal:   #0072B9 | Hover: #005A9E
    # Verde Destaque:   #27AE60 | Hover: #229954
    # Painel Escuro:    #2C3E50
    # Fundo Claro:      #F5F5F5
    # Texto Claro:      #ECF0F1
    # Texto Escuro:     #34495E
    # Borda:            #BDC3C7
    return """
        QMainWindow, QDialog {
            background-color: #F5F5F5;
        }
        QWidget {
            font-family: "Segoe UI";
            color: #34495E;
        }

        #PainelEsquerdo {
            background-color: #2C3E50; /* Cor de fundo escura para o painel */
        }
        
        #PainelEsquerdo QLabel {
            color: #ECF0F1; /* Texto claro para os títulos no painel esquerdo */
            font-weight: bold;
        }

        /* --- BOTÕES PADRÃO --- */
        QPushButton {
            background-color: #0072B9; /* Azul principal */
            color: #FFFFFF;
            border: none;
            padding: 8px; /* Reduzido um pouco o padding para dar mais espaço */
            text-align: left;
            font-size: 10pt; /* Reduzido um pouco a fonte */
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #005A9E; /* Azul mais escuro no hover */
        }
        QPushButton:pressed {
            background-color: #004578; /* Azul ainda mais escuro ao pressionar */
        }
        QPushButton:disabled {
            background-color: #95A5A6;
            color: #BDC3C7;
        }

        /* --- ESTILO DO BOTÃO DE MANUTENÇÃO PREVENTIVA --- */
        #BotaoManutencaoPreventiva {
            background-color: #27AE60; /* Verde para destaque */
            font-size: 11pt; /* Mantém a fonte maior para o botão principal */
            font-weight: bold;
        }
        #BotaoManutencaoPreventiva:hover {
            background-color: #229954; /* Verde mais escuro no hover */
        }
        #BotaoManutencaoPreventiva:pressed {
            background-color: #1E8449; /* Verde ainda mais escuro ao pressionar */
        }

        /* --- PAINEL DIREITO (LOG) --- */
        QTextEdit {
            background-color: #FFFFFF;
            border: 1px solid #BDC3C7;
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
            background-color: #0072B9;
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
        #LabelLogo { margin-bottom: 10px; }
        #LabelTituloSobre {
            font-size: 14pt;
            font-weight: bold;
            margin-bottom: 5px;
        }
        #LabelVersaoSobre {
            font-size: 10pt;
            color: #7F8C8D;
            margin-bottom: 15px;
        }
        
        /* NOVO: Estilo para a Área de Rolagem e seu conteúdo */
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        /* O #ScrollAreaContainer é o QWidget que está DENTRO da QScrollArea */
        #ScrollAreaContainer {
            background-color: #F5F5F5;
        }
        #ScrollAreaContainer QLabel {
            color: #34495E; /* Garante que os títulos dentro da rolagem usem a cor correta */
        }
    """

# --- Ponto de Entrada da Aplicação ---
if __name__ == '__main__':
    if not e_administrador():
        # Inicializa uma app temporária apenas para mostrar o QMessageBox
        app_temp = QApplication(sys.argv)
        QMessageBox.critical(None, "Erro de Permissão", "Esta aplicação precisa ser executada como Administrador para funcionar corretamente.")
        sys.exit(1)

    configurar_ambiente()
    configurar_logs()

    app = QApplication(sys.argv)
    app.setStyleSheet(obter_stylesheet())

    # --- LÓGICA DE TAMANHO RESPONSIVO ---
    janela = JanelaPrincipal()
    
    # Obtém a geometria da tela principal
    screen = app.primaryScreen()
    if screen:
        available_geometry = screen.availableGeometry()
        # Define o tamanho da janela como uma porcentagem do espaço disponível
        janela.resize(int(available_geometry.width() * 0.8), int(available_geometry.height() * 0.9))
        # Define um tamanho mínimo para evitar que a janela fique inútil
        janela.setMinimumSize(800, 600)
    
    janela.show()
    sys.exit(app.exec())