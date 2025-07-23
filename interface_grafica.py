# interface_grafica.py
import socket
import logging
import time
import os
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QProgressBar, QMessageBox, QInputDialog, QDialog,
    QDialogButtonBox, QFormLayout, QLineEdit
)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap
import qtawesome as qta

# Importa as funções de backend e constantes
from backend import (
    DIRETORIO_APP_DATA, ARQUIVO_CONFIG,
    renomear_computador, aplicar_gpos_fct, aplicar_tema_fct,
    restaurar_gpos_padrao, forcar_atualizacao_gpos, resetar_microsoft_store,
    habilitar_acesso_smb_legado, iniciar_limpeza_sistema, gerenciar_widget_desktop
)

# Classe GerenciadorConfig
class GerenciadorConfig:
    """Carrega e salva as configurações da aplicação em um arquivo JSON."""
    def __init__(self, caminho_arquivo=ARQUIVO_CONFIG):
        self.caminho_arquivo = caminho_arquivo
        self.padroes = {
            "CAMINHO_TEMA": r"\\fog\gpos\fct-labs.deskthemepack",
            "CAMINHO_BASE_GPO": r"\\fog\gpos",
            "URL_BLEACHBIT": "https://download.bleachbit.org/BleachBit-5.0.0-portable.zip",
        }

    def carregar(self):
        if not os.path.exists(self.caminho_arquivo):
            self.salvar(self.padroes)
        try:
            with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # Garante que todas as chaves padrão existam
            for chave, valor in self.padroes.items():
                config.setdefault(chave, valor)
            return config
        except (json.JSONDecodeError, IOError):
            self.salvar(self.padroes)
            return self.padroes

    def salvar(self, dados):
        with open(self.caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4)


# Classe DialogoConfig
class DialogoConfig(QDialog):
    """Janela de diálogo para editar as configurações."""
    def __init__(self, gerenciador_config, parent=None):
        super().__init__(parent)
        self.gerenciador = gerenciador_config
        self.config_atual = self.gerenciador.carregar()

        self.setWindowTitle("Configurações")
        self.setMinimumWidth(500)
        self.layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.entradas = {}
        for chave, valor in self.config_atual.items():
            campo_texto = QLineEdit(valor)
            form_layout.addRow(QLabel(chave.replace("_", " ").title() + ":"), campo_texto)
            self.entradas[chave] = campo_texto
        self.layout.addLayout(form_layout)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.salvar_e_fechar)
        botoes.rejected.connect(self.reject)
        self.layout.addWidget(botoes)

    def salvar_e_fechar(self):
        for chave, campo_texto in self.entradas.items():
            self.config_atual[chave] = campo_texto.text()
        self.gerenciador.salvar(self.config_atual)
        self.accept()


# --- NOVO: Janela "Sobre" ---
class DialogoSobre(QDialog):
    """Janela de diálogo com informações sobre a aplicação."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo da Unidade
        label_logo = QLabel()
        label_logo.setObjectName("LabelLogo")
        if os.path.exists("logo.png"):
            pixmap = QPixmap("logo.png")
            label_logo.setPixmap(pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            label_logo.setText("Logo não encontrado\n(adicione logo.png)")
            label_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_logo, alignment=Qt.AlignmentFlag.AlignCenter)

        # Título e Versão
        titulo = QLabel("Ferramenta de Manutenção FCT/UFG")
        titulo.setObjectName("LabelTituloSobre")
        layout.addWidget(titulo, alignment=Qt.AlignmentFlag.AlignCenter)

        versao = QLabel("Versão 5.1")
        versao.setObjectName("LabelVersaoSobre")
        layout.addWidget(versao, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Botão OK
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        botoes.accepted.connect(self.accept)
        layout.addWidget(botoes, alignment=Qt.AlignmentFlag.AlignCenter)


# (A classe Worker continua a mesma)
class Worker(QObject):
    """Executa uma tarefa em uma thread separada para não travar a GUI."""
    progresso = pyqtSignal(str)
    finalizado = pyqtSignal()

    def __init__(self, funcao, *args, **kwargs):
        super().__init__()
        self.funcao = funcao
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            gerador = self.funcao(*self.args, **self.kwargs)
            for resultado in gerador:
                if resultado:
                    self.progresso.emit(str(resultado))
                time.sleep(0.05)  # Pequena pausa para a GUI atualizar
        except Exception as e:
            self.progresso.emit(f"ERRO NÃO TRATADO NA TAREFA: {e}")
        finally:
            self.finalizado.emit()


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None
        self.gerenciador_config = GerenciadorConfig()
        self.config = self.gerenciador_config.carregar()

        self.inicializar_ui()

        self.logar_no_console("Ferramenta de Manutenção FCT/UFG v5.1 pronta.")
        self.logar_no_console(f"Diretório de dados: {DIRETORIO_APP_DATA}")
        self.logar_no_console("Selecione uma ação no menu à esquerda.")

    def inicializar_ui(self):
        self.setWindowTitle("Ferramenta de Manutenção FCT/UFG")
        self.setWindowIcon(qta.icon('fa5s.tools', color='#FFFFFF'))
        self.setGeometry(100, 100, 1000, 600)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)

        # --- Painel Esquerdo (Botões de Ação) ---
        painel_esquerdo_widget = QWidget()
        painel_esquerdo_widget.setObjectName("PainelEsquerdo")
        painel_esquerdo_layout = self.criar_painel_esquerdo()
        painel_esquerdo_widget.setLayout(painel_esquerdo_layout)

        # --- Painel Direito (Console de Log) ---
        painel_direito = self.criar_painel_direito()

        layout_principal.addWidget(painel_esquerdo_widget, 1)
        layout_principal.addLayout(painel_direito, 3)

    def criar_painel_esquerdo(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        titulo = QLabel("Ações Rápidas")
        titulo.setFont(QFont("Segoe UI", 16))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Lista de botões de ações principais
        botoes_info = [
            ("Renomear PC", 'fa5s.laptop-code', self.executar_renomear_computador),
            ("Aplicar GPOs FCT", 'fa5s.university', lambda: self.executar_tarefa(aplicar_gpos_fct, self.config['CAMINHO_BASE_GPO'])),
            ("Aplicar Tema FCT", 'fa5s.palette', lambda: self.executar_tarefa(aplicar_tema_fct, self.config['CAMINHO_TEMA'])),
            ("Restaurar GPOs Padrão", 'fa5s.undo-alt', lambda: self.executar_com_confirmacao(restaurar_gpos_padrao, "Restaurar GPOs?", "Isso removerá todas as políticas locais. Deseja continuar?")),
            ("Forçar Atualização de GPOs", 'fa5s.sync-alt', lambda: self.executar_tarefa(forcar_atualizacao_gpos)),
            ("Resetar Microsoft Store", 'fa5s.store-alt', lambda: self.executar_tarefa(resetar_microsoft_store)),
            ("Habilitar SMBv1 (Só Win11)", 'fa5s.folder-open', lambda: self.executar_com_confirmacao(habilitar_acesso_smb_legado, "Habilitar SMBv1?", "Isso habilita um protocolo inseguro. Use apenas em redes confiáveis.")),
            ("Limpeza Geral do Sistema", 'fa5s.broom', lambda: self.executar_tarefa(iniciar_limpeza_sistema, self.config['URL_BLEACHBIT']))
        ]
        self.botoes_acao = []
        for texto, icone, funcao in botoes_info:
            btn = QPushButton(f" {texto}")
            btn.setIcon(qta.icon(icone, color='#FFFFFF'))
            btn.clicked.connect(funcao)
            layout.addWidget(btn)
            self.botoes_acao.append(btn)
        
        layout.addSpacing(20)
        titulo_widget = QLabel("Aviso de Desktop")
        titulo_widget.setFont(QFont("Segoe UI", 14))
        titulo_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo_widget)

        btn_add_widget = QPushButton(" Adicionar Aviso")
        btn_add_widget.setIcon(qta.icon('fa5s.plus-circle', color='#FFFFFF'))
        btn_add_widget.clicked.connect(lambda: self.executar_tarefa(gerenciar_widget_desktop, 'adicionar', self.config))
        layout.addWidget(btn_add_widget)
        self.botoes_acao.append(btn_add_widget)

        btn_rem_widget = QPushButton(" Remover Aviso")
        btn_rem_widget.setIcon(qta.icon('fa5s.minus-circle', color='#FFFFFF'))
        btn_rem_widget.clicked.connect(lambda: self.executar_com_confirmacao(lambda: gerenciar_widget_desktop('remover', self.config), "Remover Aviso?", "Isso removerá o aviso da área de trabalho e da inicialização."))
        layout.addWidget(btn_rem_widget)
        self.botoes_acao.append(btn_rem_widget)

        layout.addStretch() # Empurra os botões abaixo para o final

        # Botão de Configurações
        btn_config = QPushButton(" Configurações")
        btn_config.setIcon(qta.icon('fa5s.cog', color='#FFFFFF'))
        btn_config.clicked.connect(self.abrir_dialogo_config)
        layout.addWidget(btn_config)
        self.botoes_acao.append(btn_config)

        # --- NOVO: Botão Sobre ---
        btn_sobre = QPushButton(" Sobre")
        btn_sobre.setIcon(qta.icon('fa5s.info-circle', color='#FFFFFF'))
        btn_sobre.clicked.connect(self.abrir_dialogo_sobre)
        layout.addWidget(btn_sobre)
        self.botoes_acao.append(btn_sobre)

        return layout

    def criar_painel_direito(self):
        layout = QVBoxLayout()
        titulo_log = QLabel("Console de Saída")
        titulo_log.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        titulo_log.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setFont(QFont("Consolas", 10))

        self.barra_progresso = QProgressBar()
        self.barra_progresso.setRange(0, 0)  # Modo indeterminado
        self.barra_progresso.setVisible(False)

        layout.addWidget(titulo_log)
        layout.addWidget(self.console_log)
        layout.addWidget(self.barra_progresso)
        return layout

    def abrir_dialogo_config(self):
        dialogo = DialogoConfig(self.gerenciador_config, self)
        if dialogo.exec():
            self.logar_no_console("\n⚙️ Configurações salvas e recarregadas.")
            self.config = self.gerenciador_config.carregar()
        else:
            self.logar_no_console("\n❌ Alteração de configurações cancelada.")
    
    def abrir_dialogo_sobre(self):
        """Cria e exibe a janela 'Sobre'."""
        dialogo = DialogoSobre(self)
        dialogo.exec()

    def logar_no_console(self, mensagem):
        self.console_log.append(mensagem)
        logging.info(mensagem)
        self.console_log.verticalScrollBar().setValue(self.console_log.verticalScrollBar().maximum())

    def habilitar_ui(self, habilitado):
        for btn in self.botoes_acao:
            btn.setEnabled(habilitado)

    def ao_finalizar_tarefa(self):
        self.logar_no_console("\n✅ Tarefa concluída.")
        self.barra_progresso.setVisible(False)
        self.habilitar_ui(True)

    def executar_tarefa(self, funcao_tarefa, *args):
        self.habilitar_ui(False)
        self.barra_progresso.setVisible(True)
        self.console_log.clear()
        nome_tarefa = funcao_tarefa.__name__.replace('_', ' ').title()
        self.logar_no_console(f"🚀 Iniciando: {nome_tarefa}...")

        self.thread = QThread()
        self.worker = Worker(funcao_tarefa, *args)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finalizado.connect(self.thread.quit)
        self.worker.finalizado.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progresso.connect(self.logar_no_console)
        self.thread.finished.connect(self.ao_finalizar_tarefa)

        self.thread.start()

    def executar_com_confirmacao(self, funcao_tarefa, titulo, texto, *args):
        resposta = QMessageBox.question(self, titulo, texto,
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No)
        if resposta == QMessageBox.StandardButton.Yes:
            self.executar_tarefa(lambda: funcao_tarefa(*args))

    def executar_renomear_computador(self):
        nome_atual = socket.gethostname()
        novo_nome, ok = QInputDialog.getText(self, "Alterar Nome do Computador",
                                              f"Nome atual: {nome_atual}\n\nDigite o novo nome:",
                                              text=nome_atual)
        if ok and novo_nome and novo_nome != nome_atual:
            if 1 <= len(novo_nome) <= 15 and novo_nome.replace('-', '').isalnum():
                 self.executar_tarefa(renomear_computador, novo_nome)
            else:
                QMessageBox.warning(self, "Nome Inválido", "O nome deve ter de 1 a 15 caracteres alfanuméricos (e hífens).")