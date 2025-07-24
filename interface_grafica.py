# interface_grafica.py
import socket
import logging
import time
import os
import json
import sys

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
    iniciar_limpeza_sistema, gerenciar_widget_desktop,
    manutencao_preventiva_1_click, baixar_recursos_necessarios
)

# Classe GerenciadorConfig
class GerenciadorConfig:
    """Carrega e salva as configurações da aplicação em um arquivo JSON."""
    def __init__(self, caminho_arquivo=ARQUIVO_CONFIG):
        self.caminho_arquivo = caminho_arquivo
        self.padroes = {
            "CAMINHO_TEMA": os.path.join(DIRETORIO_APP_DATA, "fct-labs.deskthemepack"),
            "CAMINHO_BASE_GPO": DIRETORIO_APP_DATA,
            "URL_BLEACHBIT": "https://download.bleachbit.org/BleachBit-5.0.0-portable.zip",
            "URL_REPOSITORIO_FCT": "https://github.com/ti-fct/Suporte-Cercomp/releases/download/2.2/"
        }

    def carregar(self):
        if not os.path.exists(self.caminho_arquivo):
            self.salvar(self.padroes)
        try:
            with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
                config = json.load(f)
            for chave, valor in self.padroes.items():
                config.setdefault(chave, valor)
            return config
        except (json.JSONDecodeError, IOError):
            return self.padroes

    def salvar(self, dados):
        with open(self.caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4)
    
    # --- NOVO: Função para resetar configurações ---
    def resetar_para_padroes(self):
        """Salva o dicionário de padrões, efetivamente resetando o arquivo de configuração."""
        self.salvar(self.padroes)


# --- ATUALIZADO: Classe DialogoConfig ---
class DialogoConfig(QDialog):
    """Janela de diálogo para editar as configurações."""
    def __init__(self, gerenciador_config, parent=None):
        super().__init__(parent)
        self.gerenciador = gerenciador_config
        self.config_atual = self.gerenciador.carregar()

        self.setWindowTitle("Configurações")
        self.setMinimumWidth(550)
        self.layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.entradas = {}
        for chave, valor in self.config_atual.items():
            campo_texto = QLineEdit(valor)
            campo_texto.setToolTip(f"Valor padrão: {self.gerenciador.padroes.get(chave, 'N/A')}")
            form_layout.addRow(QLabel(chave.replace("_", " ").title() + ":"), campo_texto)
            self.entradas[chave] = campo_texto
        self.layout.addLayout(form_layout)

        # Adiciona os botões, incluindo o de Reset
        self.botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Reset
        )
        # Renomeia o botão de Reset para um texto mais claro
        self.botoes.button(QDialogButtonBox.StandardButton.Reset).setText("Restaurar Padrões")
        
        self.botoes.accepted.connect(self.salvar_e_fechar)
        self.botoes.rejected.connect(self.reject)
        # Conecta o sinal 'clicked' a um manipulador para tratar o botão de reset
        self.botoes.clicked.connect(self.gerenciar_clique_botao)
        
        self.layout.addWidget(self.botoes)

    def salvar_e_fechar(self):
        for chave, campo_texto in self.entradas.items():
            self.config_atual[chave] = campo_texto.text()
        self.gerenciador.salvar(self.config_atual)
        self.accept()

    def gerenciar_clique_botao(self, button):
        """Verifica qual botão foi clicado e age de acordo."""
        # Pega a "role" (função) do botão que foi clicado
        if self.botoes.buttonRole(button) == QDialogButtonBox.ButtonRole.ResetRole:
            self.resetar_configuracoes()

    def resetar_configuracoes(self):
        """Pede confirmação e reseta as configurações para o padrão."""
        confirmacao = QMessageBox.question(
            self,
            "Restaurar Padrões",
            "Você tem certeza que deseja restaurar todas as configurações para os valores padrão?\nAs personalizações atuais serão perdidas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirmacao == QMessageBox.StandardButton.Yes:
            self.gerenciador.resetar_para_padroes()
            # Recarrega os padrões para garantir que estão atualizados
            novos_padroes = self.gerenciador.carregar() 
            # Atualiza os campos de texto na tela com os novos valores
            for chave, campo_texto in self.entradas.items():
                campo_texto.setText(novos_padroes.get(chave, ""))
            QMessageBox.information(self, "Sucesso", "As configurações foram restauradas para o padrão.")


# --- Janela "Sobre" ---
class DialogoSobre(QDialog):
    """Janela de diálogo com informações sobre a aplicação."""
    def __init__(self, caminho_logo,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label_logo = QLabel()
        label_logo.setObjectName("LabelLogo")
        if os.path.exists(caminho_logo):
            pixmap = QPixmap(caminho_logo)
            label_logo.setPixmap(pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            label_logo.setText("Logo não encontrado\n(logo.png)")
        layout.addWidget(label_logo, alignment=Qt.AlignmentFlag.AlignCenter)

        titulo = QLabel("Ferramenta de Manutenção FCT/UFG")
        titulo.setObjectName("LabelTituloSobre")
        layout.addWidget(titulo, alignment=Qt.AlignmentFlag.AlignCenter)

        versao = QLabel("Versão 2.2") # Versão atualizada
        versao.setObjectName("LabelVersaoSobre")
        layout.addWidget(versao, alignment=Qt.AlignmentFlag.AlignCenter)
        
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        botoes.accepted.connect(self.accept)
        layout.addWidget(botoes, alignment=Qt.AlignmentFlag.AlignCenter)


# Classe Worker (sem alterações)
class Worker(QObject):
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
                if resultado: self.progresso.emit(str(resultado))
                time.sleep(0.05)
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
        self.logar_no_console("Ferramenta de Manutenção FCT/UFG pronta.")
        self.logar_no_console(f"Diretório de dados: {DIRETORIO_APP_DATA}")
        self.logar_no_console("Selecione uma ação no menu à esquerda.")

    def inicializar_ui(self):
        self.setWindowTitle("Ferramenta de Manutenção FCT/UFG")
        self.setWindowIcon(qta.icon('fa5s.tools', color='#FFFFFF'))
        self.setGeometry(100, 100, 1000, 600)
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)
        painel_esquerdo_widget = QWidget()
        painel_esquerdo_widget.setObjectName("PainelEsquerdo")
        painel_esquerdo_layout = self.criar_painel_esquerdo()
        painel_esquerdo_widget.setLayout(painel_esquerdo_layout)
        painel_direito = self.criar_painel_direito()
        layout_principal.addWidget(painel_esquerdo_widget, 1)
        layout_principal.addLayout(painel_direito, 3)

    # --- ATUALIZADO: criar_painel_esquerdo ---
    def criar_painel_esquerdo(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        btn_manutencao_completa = QPushButton(" Manutenção 1 Clique ")
        btn_manutencao_completa.setIcon(qta.icon('fa5s.rocket', color='#FFFFFF'))
        btn_manutencao_completa.setObjectName("BotaoManutencaoPreventiva")
        
        texto_confirmacao = (
            "Esta ação executará TODAS as seguintes tarefas:\n\n"
            "- Baixar/Atualizar arquivos da FCT (GPOs, Tema)\n"
            "- Restaurar GPOs Padrão\n"
            "- Forçar Atualização de GPOs\n"
            "- Limpeza Geral do Sistema\n"
            "- Limpeza das pastas Desktop/Downloads do usuário\n"
            "- Aplicar Tema FCT\n"
            "- Aplicar GPOs FCT\n\n"
            "O processo pode demorar vários minutos. Deseja continuar?"
        )
        btn_manutencao_completa.clicked.connect(lambda: self.executar_com_confirmacao(
            manutencao_preventiva_1_click,
            "Confirmar Manutenção Completa",
            texto_confirmacao,
            self.config
        ))

        titulo_widget_preventiva = QLabel("Manutenção Preventiva")
        titulo_widget_preventiva.setFont(QFont("Segoe UI", 14))
        titulo_widget_preventiva.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo_widget_preventiva)
        layout.addWidget(btn_manutencao_completa)
        layout.addSpacing(15)
        
        titulo_acoes = QLabel("Ações Individuais")
        titulo_acoes.setFont(QFont("Segoe UI", 16))
        titulo_acoes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo_acoes)

        botoes_info = [
            ("Renomear PC", 'fa5s.laptop-code', self.executar_renomear_computador),
            ("Aplicar GPOs FCT", 'fa5s.university', lambda: self.executar_tarefa(aplicar_gpos_fct, self.config['CAMINHO_BASE_GPO'])),
            ("Aplicar Tema FCT", 'fa5s.palette', lambda: self.executar_tarefa(aplicar_tema_fct, self.config['CAMINHO_TEMA'])),
            ("Restaurar GPOs Padrão", 'fa5s.undo-alt', lambda: self.executar_com_confirmacao(restaurar_gpos_padrao, "Restaurar GPOs?", "Isso removerá todas as políticas locais.")),
            ("Forçar Atualização de GPOs", 'fa5s.sync-alt', lambda: self.executar_tarefa(forcar_atualizacao_gpos)),
            ("Resetar Microsoft Store", 'fa5s.store-alt', lambda: self.executar_tarefa(resetar_microsoft_store)),
            ("Limpeza Geral do Sistema", 'fa5s.broom', lambda: self.executar_tarefa(iniciar_limpeza_sistema, self.config['URL_BLEACHBIT']))
        ]
        self.botoes_acao = [btn_manutencao_completa]
        for texto, icone, funcao in botoes_info:
            btn = QPushButton(f" {texto}")
            btn.setIcon(qta.icon(icone, color='#FFFFFF'))
            btn.clicked.connect(funcao)
            layout.addWidget(btn)
            self.botoes_acao.append(btn)
        
        layout.addSpacing(15)
        titulo_aviso = QLabel("Aviso de Desktop")
        titulo_aviso.setFont(QFont("Segoe UI", 14))
        titulo_aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo_aviso)

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

        layout.addStretch()

        layout.addSpacing(15)
        titulo_sistema = QLabel("Sistema")
        titulo_sistema.setFont(QFont("Segoe UI", 14))
        titulo_sistema.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo_sistema)
        
        btn_baixar_recursos = QPushButton(" Baixar Recursos FCT")
        btn_baixar_recursos.setIcon(qta.icon('fa5s.download', color='#FFFFFF'))
        btn_baixar_recursos.clicked.connect(lambda: self.executar_tarefa(baixar_recursos_necessarios, self.config['URL_REPOSITORIO_FCT']))
        layout.addWidget(btn_baixar_recursos)
        self.botoes_acao.append(btn_baixar_recursos)

        btn_config = QPushButton(" Configurações")
        btn_config.setIcon(qta.icon('fa5s.cog', color='#FFFFFF'))
        btn_config.clicked.connect(self.abrir_dialogo_config)
        layout.addWidget(btn_config)
        self.botoes_acao.append(btn_config)

        # --- BOTÃO SOBRE (RESTAURADO) ---
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
        self.barra_progresso.setRange(0, 0)
        self.barra_progresso.setVisible(False)
        layout.addWidget(titulo_log)
        layout.addWidget(self.console_log)
        layout.addWidget(self.barra_progresso)
        return layout

    def abrir_dialogo_config(self):
        dialogo = DialogoConfig(self.gerenciador_config, self)
        if dialogo.exec():
            self.logar_no_console("\n⚙️ Configurações salvas ou restauradas. Recarregando...")
            self.config = self.gerenciador_config.carregar()
        else:
            self.logar_no_console("\n❌ Operação de configurações cancelada.")
    
    def abrir_dialogo_sobre(self):
        caminho_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        caminho_logo = os.path.join(caminho_base, "logo.png")
        dialogo = DialogoSobre(caminho_logo, self)
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