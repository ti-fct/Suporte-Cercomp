# main.py
import argparse
import sys
import os
import logging
import ctypes
import unicodedata
from collections.abc import Callable, Generator

from PyQt6.QtWidgets import QApplication, QMessageBox
from interface_grafica import JanelaPrincipal
from backend import (
    DIRETORIO_APP_DATA,
    DIRETORIO_LOGS,
    ajustar_melhor_desempenho,
    aplicar_gpos_fct,
    aplicar_tema_fct,
    baixar_recursos_necessarios,
    desabilitar_escrita_desktop,
    forcar_atualizacao_gpos,
    gerenciar_widget_desktop,
    habilitar_escrita_desktop,
    iniciar_limpeza_sistema,
    instalar_antivirus_apex,
    manutencao_preventiva_1_click,
    renomear_computador,
    resetar_microsoft_store,
    restaurar_gpos_padrao,
)

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
    except (AttributeError, OSError):
        return False


def normalizar_nome_acao(nome: str) -> str:
    """Converte o texto de um botão para um identificador de ação."""
    texto_normalizado = unicodedata.normalize("NFD", nome.strip().lower())
    texto_sem_acentos = "".join(
        caractere
        for caractere in texto_normalizado
        if unicodedata.category(caractere) != "Mn"
    )
    return "-".join("".join(
        caractere if caractere.isalnum() else " "
        for caractere in texto_sem_acentos
    ).split())


def criar_acoes_cli(config: dict[str, str]) -> dict[str, Callable[[], Generator[str, None, None]]]:
    """Cria o catálogo de ações disponíveis pela linha de comando."""
    return {
        "manutencao-1-clique": lambda: manutencao_preventiva_1_click(config),
        "aplicar-gpos-fct": lambda: aplicar_gpos_fct(config["CAMINHO_BASE_GPO"]),
        "aplicar-tema-fct": lambda: aplicar_tema_fct(config["CAMINHO_TEMA"]),
        "restaurar-gpos-padrao": restaurar_gpos_padrao,
        "forcar-atualizacao-de-gpos": forcar_atualizacao_gpos,
        "verificar-instalar-antivirus": instalar_antivirus_apex,
        "resetar-microsoft-store": resetar_microsoft_store,
        "ajustar-melhor-desempenho": ajustar_melhor_desempenho,
        "limpeza-geral-do-sistema": lambda: iniciar_limpeza_sistema(
            config["URL_BLEACHBIT"]
        ),
        "habilitar-escrita-no-desktop": habilitar_escrita_desktop,
        "desabilitar-escrita-no-desktop": desabilitar_escrita_desktop,
        "adicionar-aviso": lambda: gerenciar_widget_desktop("adicionar", config),
        "remover-aviso": lambda: gerenciar_widget_desktop("remover", config),
        "baixar-recursos-fct": lambda: baixar_recursos_necessarios(
            config["URL_REPOSITORIO_FCT"]
        ),
    }


def executar_acao_cli(nome_acao: str, novo_nome: str | None) -> int:
    """Executa uma ação, imprime seu progresso e retorna o código de saída."""
    from interface_grafica import GerenciadorConfig

    configurar_ambiente()
    configurar_logs()
    config = GerenciadorConfig().carregar()
    chave_acao = normalizar_nome_acao(nome_acao)
    acoes = criar_acoes_cli(config)

    if chave_acao == "renomear-pc":
        if not novo_nome:
            print("ERRO: informe o novo nome com --nome.", file=sys.stderr)
            return 2
        if not 1 <= len(novo_nome) <= 15 or not novo_nome.replace("-", "").isalnum():
            print(
                "ERRO: --nome deve ter de 1 a 15 caracteres alfanuméricos ou hífens.",
                file=sys.stderr,
            )
            return 2
        tarefa = lambda: renomear_computador(novo_nome)
    else:
        tarefa = acoes.get(chave_acao)

    if tarefa is None:
        opcoes = ", ".join(sorted([*acoes, "renomear-pc"]))
        print(f"ERRO: ação desconhecida: {nome_acao}", file=sys.stderr)
        print(f"Ações disponíveis: {opcoes}", file=sys.stderr)
        return 2

    try:
        for mensagem in tarefa():
            if mensagem:
                print(mensagem)
                logging.info(mensagem)
    except Exception as erro:
        logging.exception("Erro não tratado ao executar a ação CLI.")
        print(f"ERRO CRÍTICO: {erro}", file=sys.stderr)
        return 1

    return 0


def criar_parser_argumentos() -> argparse.ArgumentParser:
    """Configura os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Ferramenta de Manutenção FCT/UFG",
        epilog=(
            "Exemplo: Suporte-Cercomp.exe aplicar-gpos-fct\n"
            "Exemplo: Suporte-Cercomp.exe \"Renomear PC\" --nome FCT-LAB-01\n\n"
            "Ações: manutencao-1-clique, renomear-pc, aplicar-gpos-fct,\n"
            "aplicar-tema-fct, restaurar-gpos-padrao, forcar-atualizacao-de-gpos,\n"
            "verificar-instalar-antivirus, resetar-microsoft-store,\n"
            "ajustar-melhor-desempenho, limpeza-geral-do-sistema,\n"
            "habilitar-escrita-no-desktop, desabilitar-escrita-no-desktop,\n"
            "adicionar-aviso, remover-aviso, baixar-recursos-fct."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "acao",
        nargs="?",
        help="Nome do botão ou identificador da ação. Sem valor, abre a interface.",
    )
    parser.add_argument(
        "--nome",
        help="Novo nome do computador; obrigatório para 'Renomear PC'.",
    )
    return parser

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
def iniciar_interface() -> None:
    """Inicializa a interface gráfica da aplicação."""
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


def main() -> int:
    """Seleciona entre o modo gráfico e o modo de linha de comando."""
    argumentos = criar_parser_argumentos().parse_args()

    if not argumentos.acao:
        iniciar_interface()
        return 0

    if not e_administrador():
        print(
            "ERRO: esta ação precisa ser executada como Administrador.",
            file=sys.stderr,
        )
        return 1

    return executar_acao_cli(argumentos.acao, argumentos.nome)


if __name__ == "__main__":
    sys.exit(main())
