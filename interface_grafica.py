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
    QDialogButtonBox, QFormLayout, QLineEdit, QScrollArea
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
    manutencao_preventiva_1_click, baixar_recursos_necessarios,
    habilitar_escrita_desktop, desabilitar_escrita_desktop
)

# Constante com a versão atual do software
# Alterar sempre que lançar uma nova versão
APP_VERSION = "3.1.0" 

class GerenciadorConfig:
    """Carrega e salva as configurações da aplicação em um arquivo JSON."""
    def __init__(self, caminho_arquivo=ARQUIVO_CONFIG):
        self.caminho_arquivo = caminho_arquivo
        self.padroes = {
            "APP_VERSION": APP_VERSION,
            "CAMINHO_TEMA": os.path.join(DIRETORIO_APP_DATA, "fct-labs.deskthemepack"),
            "CAMINHO_BASE_GPO": DIRETORIO_APP_DATA,
            "URL_BLEACHBIT": "https://download.bleachbit.org/BleachBit-5.0.0-portable.zip",
            "URL_REPOSITORIO_FCT": "https://github.com/ti-fct/Suporte-Cercomp/releases/download/recursos/",
            "URL_PYTHON_WIDGET": "https://github.com/ti-fct/Suporte-Cercomp/releases/download/recursos/python-widget.zip"
        }

    def carregar(self, log_callback=None):
        """
        Carrega a configuração. Se a versão for antiga, reseta para o padrão.
        Opcionalmente, usa um callback para logar mensagens na UI.
        """
        if not os.path.exists(self.caminho_arquivo):
            self.salvar(self.padroes)
            return self.padroes.copy()

        config = {}
        try:
            with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            if log_callback:
                log_callback("AVISO: Arquivo de configuração corrompido. Restaurando para o padrão.")
            self.salvar(self.padroes)
            return self.padroes.copy()

        versao_config = config.get("APP_VERSION", "0.0.0")
        
        if versao_config < APP_VERSION:
            if log_callback:
                log_callback(f"INFO: Nova versão detectada ({APP_VERSION}). Restaurando configurações para o padrão.")
            self.salvar(self.padroes)
            return self.padroes.copy()

        return config

    def salvar(self, dados):
        os.makedirs(os.path.dirname(self.caminho_arquivo), exist_ok=True)
        with open(self.caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4)
    
    def resetar_para_padroes(self):
        self.salvar(self.padroes)

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
        # Garante que a ordem seja consistente
        for chave in sorted(self.config_atual.keys()):
            # Não exibe chaves de controle interno para o usuário
            if chave in ["APP_VERSION", "salvamento_desktop_habilitado"]:
                continue
            valor = self.config_atual[chave]
            campo_texto = QLineEdit(valor)
            campo_texto.setToolTip(f"Valor padrão: {self.gerenciador.padroes.get(chave, 'N/A')}")
            # Melhora a legibilidade da chave
            label_texto = chave.replace("_", " ").replace("Url", "URL").title()
            form_layout.addRow(QLabel(label_texto + ":"), campo_texto)
            self.entradas[chave] = campo_texto
        self.layout.addLayout(form_layout)

        self.botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Reset
        )
        self.botoes.button(QDialogButtonBox.StandardButton.Reset).setText("Restaurar Padrões")
        
        self.botoes.accepted.connect(self.salvar_e_fechar)
        self.botoes.rejected.connect(self.reject)
        self.botoes.clicked.connect(self.gerenciar_clique_botao)
        
        self.layout.addWidget(self.botoes)

    def salvar_e_fechar(self):
        for chave, campo_texto in self.entradas.items():
            self.config_atual[chave] = campo_texto.text()
        self.gerenciador.salvar(self.config_atual)
        self.accept()

    def gerenciar_clique_botao(self, button):
        if self.botoes.buttonRole(button) == QDialogButtonBox.ButtonRole.ResetRole:
            self.resetar_configuracoes()

    def resetar_configuracoes(self):
        confirmacao = QMessageBox.question(
            self,
            "Restaurar Padrões",
            "Você tem certeza que deseja restaurar todas as configurações para os valores padrão?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirmacao == QMessageBox.StandardButton.Yes:
            self.gerenciador.resetar_para_padroes()
            novos_padroes = self.gerenciador.carregar() 
            for chave, campo_texto in self.entradas.items():
                campo_texto.setText(novos_padroes.get(chave, ""))
            QMessageBox.information(self, "Sucesso", "As configurações foram restauradas para o padrão.")


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
            label_logo.setText("Logo não encontrado\n(assets/logo.png)")
        layout.addWidget(label_logo, alignment=Qt.AlignmentFlag.AlignCenter)

        titulo = QLabel("Ferramenta de Manutenção FCT/UFG")
        titulo.setObjectName("LabelTituloSobre")
        layout.addWidget(titulo, alignment=Qt.AlignmentFlag.AlignCenter)

        versao = QLabel(f"Versão {APP_VERSION}") 
        versao.setObjectName("LabelVersaoSobre")
        layout.addWidget(versao, alignment=Qt.AlignmentFlag.AlignCenter)
        
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        botoes.accepted.connect(self.accept)
        layout.addWidget(botoes, alignment=Qt.AlignmentFlag.AlignCenter)


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
            resultado = self.funcao(*self.args, **self.kwargs)
            if hasattr(resultado, '__iter__') and not isinstance(resultado, (str, bytes)):
                for linha in resultado:
                    if linha: self.progresso.emit(str(linha))
                    time.sleep(0.05)
            elif resultado:
                 self.progresso.emit(str(resultado))
        except Exception as e:
            self.progresso.emit(f"ERRO NÃO TRATADO NA TAREFA: {e}")
            logging.error(f"Erro na thread worker: {e}", exc_info=True)
        finally:
            self.finalizado.emit()
            
class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None
        self.gerenciador_config = GerenciadorConfig()

        self.inicializar_ui()

        self.config = self.gerenciador_config.carregar(log_callback=self.logar_no_console)
        
        self.logar_no_console("--------------------------------------------------")
        self.logar_no_console("Ferramenta de Manutenção FCT/UFG pronta.")
        self.logar_no_console(f"Diretório de dados: {DIRETORIO_APP_DATA}")
        self.logar_no_console("Selecione uma ação no menu à esquerda.")

    def inicializar_ui(self):
        self.setWindowTitle("Ferramenta de Manutenção FCT/UFG")
        self.setWindowIcon(qta.icon('fa5s.tools', color='#FFFFFF'))
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)
        painel_esquerdo_scroll = self.criar_painel_esquerdo()
        painel_direito = self.criar_painel_direito()
        layout_principal.addWidget(painel_esquerdo_scroll, 1)
        layout_principal.addLayout(painel_direito, 3)

    def criar_painel_esquerdo(self):
        container_widget = QWidget()
        container_widget.setObjectName("ScrollAreaContainer")
        layout = QVBoxLayout(container_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        btn_manutencao_completa = QPushButton(" Manutenção 1 Clique ")
        btn_manutencao_completa.setIcon(qta.icon('fa5s.rocket', color='#FFFFFF'))
        btn_manutencao_completa.setObjectName("BotaoManutencaoPreventiva")
        texto_confirmacao_manutencao = (
            "Esta ação executará várias tarefas de manutenção em sequência.\n"
            "O processo pode demorar vários minutos. Deseja continuar?"
        )
        btn_manutencao_completa.clicked.connect(lambda: self.executar_com_confirmacao(
            manutencao_preventiva_1_click,
            "Confirmar Manutenção Completa", texto_confirmacao_manutencao, self.config
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
            ("Limpeza Geral do Sistema", 'fa5s.broom', lambda: self.executar_tarefa(iniciar_limpeza_sistema, self.config['URL_BLEACHBIT'])),
        ]
        self.botoes_acao = [btn_manutencao_completa]
        for texto, icone, funcao in botoes_info:
            btn = QPushButton(f" {texto}")
            btn.setIcon(qta.icon(icone, color='#FFFFFF'))
            btn.clicked.connect(funcao)
            layout.addWidget(btn)
            self.botoes_acao.append(btn)
        
        layout.addSpacing(15)
        titulo_seguranca = QLabel("Controles de Segurança")
        titulo_seguranca.setFont(QFont("Segoe UI", 14))
        titulo_seguranca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo_seguranca)

        btn_habilitar_escrita = QPushButton(" Habilitar Escrita no Desktop")
        btn_habilitar_escrita.setIcon(qta.icon('fa5s.lock-open', color='#FFFFFF'))
        btn_habilitar_escrita.clicked.connect(lambda: self.executar_com_confirmacao(
            habilitar_escrita_desktop, "Habilitar Escrita?", 
            "Isso concederá permissão total de escrita na Área de Trabalho para o usuário atual.\nDeseja continuar?"
        ))
        layout.addWidget(btn_habilitar_escrita)
        self.botoes_acao.append(btn_habilitar_escrita)

        btn_desabilitar_escrita = QPushButton(" Desabilitar Escrita no Desktop")
        btn_desabilitar_escrita.setIcon(qta.icon('fa5s.lock', color='#FFFFFF'))
        btn_desabilitar_escrita.clicked.connect(lambda: self.executar_com_confirmacao(
            desabilitar_escrita_desktop, "Desabilitar Escrita?", 
            "Isso NEGARÁ a permissão de escrita na Área de Trabalho para o usuário atual.\nDeseja continuar?"
        ))
        layout.addWidget(btn_desabilitar_escrita)
        self.botoes_acao.append(btn_desabilitar_escrita)

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
        btn_sobre = QPushButton(" Sobre")
        btn_sobre.setIcon(qta.icon('fa5s.info-circle', color='#FFFFFF'))
        btn_sobre.clicked.connect(self.abrir_dialogo_sobre)
        layout.addWidget(btn_sobre)
        self.botoes_acao.append(btn_sobre)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(container_widget)
        
        return scroll_area

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
            self.logar_no_console("\n⚙️ Configurações salvas. Recarregando...")
            self.config = self.gerenciador_config.carregar(log_callback=self.logar_no_console)
        else:
            self.logar_no_console("\n❌ Operação de configurações cancelada.")
    
    def abrir_dialogo_sobre(self):
        caminho_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        caminho_logo = os.path.join(caminho_base, "assets", "logo.png")
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
        self.config = self.gerenciador_config.carregar(log_callback=self.logar_no_console)
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
            self.executar_tarefa(funcao_tarefa, *args)

    def executar_renomear_computador(self):
        nome_atual = socket.gethostname()
        novo_nome, ok = QInputDialog.getText(self, "Alterar Nome do Computador",
                                              f"Nome atual: {nome_atual}\n\nDigite o novo nome:",
                                              text=nome_atual)
        if ok and novo_nome and novo_nome.strip() and novo_nome != nome_atual:
            if 1 <= len(novo_nome) <= 15 and novo_nome.replace('-', '').isalnum():
                 self.executar_tarefa(renomear_computador, novo_nome)
            else:
                QMessageBox.warning(self, "Nome Inválido", "O nome deve ter de 1 a 15 caracteres alfanuméricos (e hífens).")