# backend.py
import os
import subprocess
import shutil
import json
import requests
import zipfile
import winreg
import sys
import time
import ctypes

# --- Constantes de Configuração ---
DIRETORIO_APP_DATA = r"C:\ProgramData\Suporte-Cercomp"
DIRETORIO_LOGS = os.path.join(DIRETORIO_APP_DATA, "logs")
ARQUIVO_CONFIG = os.path.join(DIRETORIO_APP_DATA, "config.json")
CAMINHO_SCRIPT_WIDGET = os.path.join(DIRETORIO_APP_DATA, "AvisoDesktop.pyw")
DIRETORIO_PYTHON_WIDGET = os.path.join(DIRETORIO_APP_DATA, "python_widget_env")
REGISTRO_WIDGET = r"Software\Microsoft\Windows\CurrentVersion\Run"
CHAVE_REGISTRO_WIDGET = "FCT_UFG_DesktopInfo"

# ... (O CONTEUDO_SCRIPT_WIDGET permanece o mesmo) ...
CONTEUDO_SCRIPT_WIDGET = """
# Aviso Desktop
import sys
import socket
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
    from PyQt6.QtCore import Qt, QEvent, QTimer
    from PyQt6.QtGui import QColor
except ImportError:
    sys.exit()

class WidgetInfo(QWidget):
    def __init__(self):
        super().__init__()
        self.configurar_interface()

    def configurar_interface(self):
        self.setWindowTitle("WidgetInfo")
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

# --- Funções Lógicas ---

def executar_comando_powershell(comando, timeout=180):
    """Executa um comando PowerShell."""
    yield f"Executando via PowerShell: {comando[:70]}..."
    try:
        processo = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando],
            capture_output=True, text=True, encoding='utf-8', errors='ignore',
            timeout=timeout, check=False
        )
        if processo.stdout:
            yield processo.stdout.strip()
        if processo.returncode != 0:
            yield f"ERRO: Código de retorno {processo.returncode}."
            if processo.stderr:
                yield f"Detalhes: {processo.stderr.strip()}"
    except Exception as e:
        yield f"ERRO CRÍTICO (PowerShell): {e}"

def executar_comando_cmd(comando, timeout=180, work_dir=None):
    """Executa um comando no CMD, com opção de diretório de trabalho."""
    yield f"Executando via CMD: {comando[:70]}..."
    try:
        processo = subprocess.run(
            ["cmd", "/c", comando],
            capture_output=True, text=True, encoding='oem', errors='ignore',
            timeout=timeout, check=False, cwd=work_dir,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if processo.stdout:
            yield processo.stdout.strip()
        if processo.returncode != 0:
            yield f"AVISO: Código de retorno {processo.returncode}."
            if processo.stderr:
                yield f"Saída de erro: {processo.stderr.strip()}"
    except Exception as e:
        yield f"ERRO CRÍTICO (CMD): {e}"

def _listar_usuarios_padrao():
    """
    Retorna a lista de usuários LOCAIS 'padrão' (isto é, que NÃO pertencem ao grupo de Administradores)
    """
    # Contas internas do Windows que nunca devem ser tratadas como "aluno".
    contas_sistema = "'Administrador','Administrator','Convidado','Guest','DefaultAccount','WDAGUtilityAccount','defaultuser0'"

    comando_ps = (
        "$grupoAdmins = Get-LocalGroup | Where-Object { $_.SID -like '*-544' }; "
        "$membrosAdmins = @(); "
        "if ($grupoAdmins) { "
        "$membrosAdmins = @((Get-LocalGroupMember -Group $grupoAdmins -ErrorAction SilentlyContinue) | "
        "ForEach-Object { $_.Name -replace '^.*\\\\', '' }) }; "
        f"$contasSistema = @({contas_sistema}); "
        "$usuarios = Get-LocalUser -ErrorAction SilentlyContinue | Where-Object { $_.Enabled -eq $true }; "
        "$usuariosPadrao = $usuarios | Where-Object { ($membrosAdmins -notcontains $_.Name) -and ($contasSistema -notcontains $_.Name) }; "
        "($usuariosPadrao.Name) -join ';'"
    )

    try:
        processo = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando_ps],
            capture_output=True, text=True, encoding='utf-8', errors='ignore',
            timeout=60, check=False, creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception as e:
        return [], f"ERRO CRÍTICO ao listar usuários locais: {e}"

    if processo.returncode != 0:
        detalhe = processo.stderr.strip() if processo.stderr else "sem detalhes adicionais"
        return [], f"ERRO CRÍTICO ao listar usuários locais (código {processo.returncode}): {detalhe}"

    nomes_brutos = (processo.stdout or "").strip()
    if not nomes_brutos:
        return [], None

    nomes_usuarios = [n.strip() for n in nomes_brutos.split(';') if n.strip()]

    usuarios_validos = []
    for nome in nomes_usuarios:
        caminho_desktop = os.path.join("C:\\Users", nome, "Desktop")
        if os.path.exists(caminho_desktop):
            usuarios_validos.append((nome, caminho_desktop))

    return usuarios_validos, None

def reiniciar_explorer():
    """Reinicia o processo do Windows Explorer."""
    yield "Reiniciando parâmetros do sistema..."
    yield from executar_comando_powershell(f"RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters ,1 ,True")
    yield "Reiniciando o Windows Explorer..."
    yield from executar_comando_cmd(f"taskkill /F /IM explorer.exe")
    time.sleep(2)  # Pequena pausa para garantir que o processo foi encerrado
    yield from executar_comando_cmd(f"start explorer.exe")
    yield from executar_comando_powershell(f"Stop-Process -Name explorer -Force; Start-Process explorer")
    yield "Windows Explorer reiniciado com sucesso."
    yield from executar_comando_cmd(f"gpupdate /force", timeout=300)
    yield "Atualização de políticas forçada."

def habilitar_escrita_desktop():
    """
    Restaura a permissão de escrita na Área de Trabalho para os usuários Padrão (não administradores)
    """
    yield "--- Habilitando Permissão de Escrita no Desktop (usuários padrão) ---"
    usuarios_padrao, erro = _listar_usuarios_padrao()
    if erro:
        yield erro
        return
    if not usuarios_padrao:
        yield "AVISO: Nenhum usuário padrão (não administrador) foi encontrado neste computador."
        return

    for nome_usuario, caminho_desktop in usuarios_padrao:
        yield f"Restaurando permissão de escrita para '{nome_usuario}' em '{caminho_desktop}'..."
        comando_remover_deny = f'icacls "{caminho_desktop}" /remove:d "{nome_usuario}" /T /C'
        yield from executar_comando_cmd(comando_remover_deny)
        comando_grant = f'icacls "{caminho_desktop}" /grant "{nome_usuario}":(F) /T /C'
        yield from executar_comando_cmd(comando_grant)

    yield "Permissão de escrita no Desktop foi HABILITADA para os usuários padrão."
    yield from reiniciar_explorer()

def desabilitar_escrita_desktop():
    """
    Remove a permissão de escrita na Área de Trabalho SOMENTE para os usuários PADRÃO (não administradores) do computador
    """
    yield "--- Desabilitando Permissão de Escrita no Desktop (usuários padrão) ---"
    usuarios_padrao, erro = _listar_usuarios_padrao()
    if erro:
        yield erro
        return
    if not usuarios_padrao:
        yield "AVISO: Nenhum usuário padrão (não administrador) foi encontrado neste computador. Nada a fazer."
        return

    for nome_usuario, caminho_desktop in usuarios_padrao:
        yield f"Negando permissão de escrita para o usuário padrão '{nome_usuario}' em '{caminho_desktop}'..."
        comando = f'icacls "{caminho_desktop}" /deny "{nome_usuario}":(W,DC) /T /C'
        yield from executar_comando_cmd(comando)

    yield "Permissão de escrita no Desktop foi DESABILITADA para os usuários padrão."
    yield "Contas de administrador não foram alteradas e permanecem com escrita habilitada."
    yield from reiniciar_explorer()

# ... (O resto das funções de backend como 'aplicar_tema_fct', 'limpar_pastas_usuario', etc. permanecem inalteradas) ...
def baixar_recursos_necessarios(url_repositorio):
    """Baixa os arquivos de configuração (GPOs, Tema) do GitHub."""
    arquivos_para_baixar = ["lgpo.exe", "machine.txt", "user.txt", "fct-labs.deskthemepack"]
    yield "Verificando e baixando recursos necessários..."
    
    if not url_repositorio.endswith('/'):
        url_repositorio += '/'
    
    for arquivo in arquivos_para_baixar:
        url_arquivo = url_repositorio + arquivo
        caminho_destino = os.path.join(DIRETORIO_APP_DATA, arquivo)
        
        yield f"Baixando '{arquivo}'..."
        try:
            with requests.get(url_arquivo, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(caminho_destino, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
        
            if not os.path.exists(caminho_destino) or os.path.getsize(caminho_destino) == 0:
                yield f"ERRO: '{arquivo}' foi baixado mas está vazio ou corrompido."
                return
                
            yield f"'{arquivo}' baixado com sucesso ({os.path.getsize(caminho_destino)} bytes)."
        except requests.exceptions.RequestException as e:
            yield f"ERRO CRÍTICO ao baixar '{arquivo}': {e}"
            return
    
    yield "Download de todos os recursos concluído."

def gerenciar_widget_desktop(acao, config):
    """Adiciona ou remove o widget de aviso do desktop."""
    pythonw_exe = os.path.join(DIRETORIO_PYTHON_WIDGET, 'pythonw.exe')
    comando_finalizar = f'taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq WidgetInfo*"'

    if acao == 'adicionar':
        url_python_widget = config.get("URL_PYTHON_WIDGET")
        if not url_python_widget:
            yield "ERRO CRÍTICO: URL para o ambiente Python do widget não configurada."
            return
        zip_path = os.path.join(DIRETORIO_APP_DATA, "python_widget_env.zip")
        yield f"Baixando ambiente Python do widget..."
        try:
            with requests.get(url_python_widget, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(zip_path, 'wb') as f: shutil.copyfileobj(r.raw, f)
        except requests.exceptions.RequestException as e:
            yield f"ERRO CRÍTICO ao baixar o ambiente do widget: {e}"; return
        yield "Extraindo ambiente Python..."
        try:
            if os.path.exists(DIRETORIO_PYTHON_WIDGET): shutil.rmtree(DIRETORIO_PYTHON_WIDGET)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(DIRETORIO_PYTHON_WIDGET)
            os.remove(zip_path)
        except Exception as e:
            yield f"ERRO CRÍTICO ao extrair o ambiente do widget: {e}"; return
        if not os.path.exists(pythonw_exe):
            yield f"ERRO CRÍTICO: 'pythonw.exe' não encontrado após extração."; return
        yield "Ambiente do widget instalado."
        yield f"Criando script do widget..."
        with open(CAMINHO_SCRIPT_WIDGET, "w", encoding="utf-8") as f: f.write(CONTEUDO_SCRIPT_WIDGET)
        yield "Adicionando à inicialização do Windows..."
        try:
            comando_reg = f'"{pythonw_exe}" "{CAMINHO_SCRIPT_WIDGET}"'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRO_WIDGET, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, CHAVE_REGISTRO_WIDGET, 0, winreg.REG_SZ, comando_reg)
            yield "Widget configurado para iniciar com o Windows."
        except Exception as e:
            yield f"ERRO ao registrar na inicialização: {e}"; return
        yield "Finalizando instâncias antigas e iniciando o widget..."
        subprocess.run(comando_finalizar, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.Popen([pythonw_exe, CAMINHO_SCRIPT_WIDGET], creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Widget adicionado e iniciado com sucesso."
    elif acao == 'remover':
        yield "Finalizando processo do widget..."
        subprocess.run(comando_finalizar, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        yield "Removendo da inicialização do Windows..."
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRO_WIDGET, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, CHAVE_REGISTRO_WIDGET)
            yield "Registro de inicialização removido."
        except FileNotFoundError: yield "AVISO: Registro de inicialização não encontrado."
        except Exception as e: yield f"ERRO ao remover do registro: {e}"
        if os.path.exists(CAMINHO_SCRIPT_WIDGET):
            try: os.remove(CAMINHO_SCRIPT_WIDGET); yield "Arquivo de script removido."
            except OSError as e: yield f"ERRO ao remover arquivo de script: {e}"
        if os.path.exists(DIRETORIO_PYTHON_WIDGET):
            try: shutil.rmtree(DIRETORIO_PYTHON_WIDGET); yield "Ambiente Python do widget removido."
            except OSError as e: yield f"ERRO ao remover diretório do widget: {e}"
        yield "Widget removido com sucesso."

def aplicar_tema_fct(caminho_tema):
    """
    Versão alternativa que aplica o tema usando múltiplas estratégias
    para detectar o usuário logado.
    """
    yield "Iniciando aplicação de tema (método alternativo)..."

    # Verificar privilégios de Administrador
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            yield "ERRO CRÍTICO: Esta função requer privilégios de Administrador."
            return
        yield "Verificação de privilégios de Administrador: OK."
    except Exception as e:
        yield f"ERRO ao verificar privilégios de Administrador: {e}"
        return

    # Validação do arquivo de tema
    if not os.path.exists(caminho_tema):
        yield f"ERRO: Arquivo de tema não encontrado: {caminho_tema}."
        return
    yield f"Arquivo de tema encontrado: {os.path.basename(caminho_tema)}"

    # Múltiplas estratégias para obter usuário logado
    usuario_logado = None
    
    # Estratégia 1: Win32_ComputerSystem
    try:
        yield "Tentativa 1: Obtendo usuário via Win32_ComputerSystem..."
        comando_ps1 = "(Get-CimInstance -ClassName Win32_ComputerSystem).Username"
        processo1 = subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando_ps1],
            capture_output=True, text=True, encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW, timeout=30
        )
        if processo1.stdout and processo1.stdout.strip():
            usuario_logado = processo1.stdout.strip()
            yield f"✓ Usuário encontrado (Método 1): {usuario_logado}"
    except Exception as e:
        yield f"Método 1 falhou: {e}"

    # Estratégia 2: query user
    if not usuario_logado:
        try:
            yield "Tentativa 2: Obtendo usuário via 'query user'..."
            processo2 = subprocess.run(
                ["query", "user"],
                capture_output=True, text=True, encoding='oem',
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=30
            )
            if processo2.stdout:
                linhas = processo2.stdout.strip().split('\n')
                for linha in linhas[1:]:  # Pular cabeçalho
                    if 'Active' in linha or 'Ativo' in linha:
                        partes = linha.split()
                        if len(partes) > 0:
                            usuario_logado = partes[0]
                            yield f"✓ Usuário encontrado (Método 2): {usuario_logado}"
                            break
        except Exception as e:
            yield f"Método 2 falhou: {e}"

    # Estratégia 3: whoami
    if not usuario_logado:
        try:
            yield "Tentativa 3: Obtendo usuário via 'whoami'..."
            processo3 = subprocess.run(
                ["whoami"],
                capture_output=True, text=True, encoding='oem',
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=30
            )
            if processo3.stdout and processo3.stdout.strip():
                whoami_result = processo3.stdout.strip()
                if '\\' in whoami_result:
                    usuario_logado = whoami_result.split('\\')[-1]
                    yield f"✓ Usuário encontrado (Método 3): {usuario_logado}"
        except Exception as e:
            yield f"Método 3 falhou: {e}"

    # Estratégia 4: Variável de ambiente
    if not usuario_logado:
        try:
            yield "Tentativa 4: Obtendo usuário via variável de ambiente..."
            usuario_env = os.environ.get('USERNAME')
            if usuario_env:
                usuario_logado = usuario_env
                yield f"✓ Usuário encontrado (Método 4): {usuario_logado}"
        except Exception as e:
            yield f"Método 4 falhou: {e}"

    # Verificar se encontrou usuário
    if not usuario_logado:
        yield "AVISO: Não foi possível determinar o usuário logado."
        yield "Tentando aplicar tema sem contexto específico de usuário..."
        
        # Aplicar tema sem usuário específico
        try:
            yield "Aplicando tema diretamente..."
            subprocess.Popen([caminho_tema], shell=True)
            yield "Tema aplicado! A janela de personalização deve abrir."
            return
        except Exception as e:
            yield f"ERRO ao aplicar tema: {e}"
            return

    # Aplicar tema com usuário específico
    yield f"Aplicando tema para o usuário: {usuario_logado}..."
    
    # Script PowerShell mais robusto
    script_aplicar = f"""
    try {{
        # Múltiplas tentativas de aplicação
        $CaminhoTema = '{caminho_tema.replace("'", "''")}'

        Write-Output "Aguardando 5 segundos antes de aplicar..."
        Start-Sleep -Seconds 5
        
        # Método 1: Start-Process simples
        try {{
            $ProcessInfo = Start-Process -FilePath 'explorer.exe' -ArgumentList "`"$CaminhoTema`"" -PassThru -ErrorAction Stop
            Write-Output "✓ Tema aplicado via Start-Process. PID: $($ProcessInfo.Id)"
        }} catch {{
            Write-Warning "Start-Process falhou: $($_.Exception.Message)"
            
            # Método 2: Invoke-Item
            try {{
                Invoke-Item -Path $CaminhoTema -ErrorAction Stop
                Write-Output "✓ Tema aplicado via Invoke-Item"
            }} catch {{
                Write-Warning "Invoke-Item falhou: $($_.Exception.Message)"
                
                # Método 3: cmd /c start
                try {{
                    cmd /c start `"Aplicar Tema`" `"$CaminhoTema`"
                    Write-Output "✓ Tema aplicado via cmd start"
                }} catch {{
                    Write-Error "Todos os métodos falharam: $($_.Exception.Message)"
                    exit 1
                }}
            }}
        }}

        Write-Output "Aguardando 7 segundos para o sistema processar o tema..."
        Start-Sleep -Seconds 7

    }} catch {{
        Write-Error "ERRO CRÍTICO ao aplicar tema: $($_.Exception.Message)"
        exit 1
    }}
    """
    
    resultado = list(executar_comando_powershell(script_aplicar))
    for linha in resultado:
        yield linha

    yield "Aplicação de tema concluída."
    yield "Se a janela 'Personalização' abrir, pode fechá-la."
    
    yield "Desativando luz noturna..."
    comandoDesativarLuzNoturna = r"""
    $path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\CloudStore\Store\Cache\DefaultAccount\`$`$windows.data.bluelightreduction.bluelightreductions\Default"
    if (Test-Path $path) {
        Set-ItemProperty -Path $path -Name Data -Value ([byte[]](0x00)) -ErrorAction SilentlyContinue
    }"""
    yield from executar_comando_powershell(comandoDesativarLuzNoturna)

    yield "Definindo wallpaper para 'Ajustar'..."
    comandoWallpaperAjustar = r"""
    Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name WallpaperStyle -Value 6
    Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name TileWallpaper -Value 0
    """
    yield from executar_comando_powershell(comandoWallpaperAjustar)

def aplicar_gpos_fct(caminho_base_gpo):
    """Aplica as políticas de grupo (GPOs) da FCT usando lgpo.exe."""
    arquivos_necessarios = [
        os.path.join(caminho_base_gpo, "lgpo.exe"),
        os.path.join(caminho_base_gpo, "machine.txt"),
        os.path.join(caminho_base_gpo, "user.txt")
    ]
    yield "Verificando arquivos de GPO necessários..."
    if not all(os.path.exists(p) for p in arquivos_necessarios):
        yield f"ERRO: Arquivos de GPO não encontrados em {caminho_base_gpo}."
        return
    
    diretorio_original = os.getcwd()
    try:
        os.chdir(caminho_base_gpo)
        yield "Aplicando política de máquina..."
        yield from executar_comando_cmd(r"lgpo.exe /t machine.txt")
        yield "Aplicando política de usuário..."
        yield from executar_comando_cmd(r"lgpo.exe /t user.txt")
        yield "Comandos de aplicação de GPOs da FCT enviados."
    except Exception as e:
        yield f"ERRO ao executar aplicação de GPO: {e}"
    finally:
        os.chdir(diretorio_original)

# CORRIGIDO: BleachBit agora é salvo em ProgramData
def iniciar_limpeza_sistema(url_ferramenta):
    """Baixa e executa o BleachBit para limpeza geral do sistema."""
    # O diretório base agora é o mesmo da aplicação
    base_dir = DIRETORIO_APP_DATA
    tool_dir = os.path.join(base_dir, "BleachBit")
    zip_path = os.path.join(base_dir, "BleachBit.zip")
    try:
        yield f"Baixando BleachBit para {base_dir}..."
        with requests.get(url_ferramenta, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f: shutil.copyfileobj(r.raw, f)
        yield f"Extraindo para {tool_dir}..."
        if os.path.exists(tool_dir): shutil.rmtree(tool_dir)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(tool_dir)
        yield "Procurando por bleachbit_console.exe..."
        caminho_executavel = next((os.path.join(r, f) for r, _, fs in os.walk(tool_dir) for f in fs if f == "bleachbit_console.exe"), None)
        if not caminho_executavel:
            yield "ERRO: bleachbit_console.exe não encontrado após a extração."; return
        yield f"Executável encontrado: {caminho_executavel}"
        yield "Listando limpadores disponíveis..."
        list_process = subprocess.run([caminho_executavel, "--list-cleaners"], capture_output=True, text=True, check=True)
        all_cleaners = list_process.stdout.split()
        cleaners_to_run = [c for c in all_cleaners if not c.startswith("deep_scan.") and c != "system.free_disk_space"]
        yield f"{len(cleaners_to_run)} limpadores selecionados. AVISO: A limpeza pode demorar."
        yield "Executando limpeza com BleachBit..."
        yield "Apagando arquivos da pasta Music..."
        comandoLimparPastaMusic = r"""Remove-Item -Path "C:\Users\Aluno\Music\*" -Recurse -Force -ErrorAction SilentlyContinue"""
        yield from executar_comando_powershell(comandoLimparPastaMusic)
        subprocess.run([caminho_executavel, "--clean"] + cleaners_to_run, check=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=600)
        yield "Limpeza completa concluída!"
    except Exception as e:
        yield f"ERRO durante a limpeza: {e}"
    finally:
        if os.path.exists(tool_dir): shutil.rmtree(tool_dir, ignore_errors=True)
        if os.path.exists(zip_path): os.remove(zip_path)

def renomear_computador(novo_nome):
    """Altera o nome do computador no sistema."""
    yield f"Tentando alterar o nome para '{novo_nome}'..."
    yield from executar_comando_powershell(f'Rename-Computer -NewName "{novo_nome}" -Force -ErrorAction Stop')
    yield "Nome alterado! É necessário reiniciar para aplicar."

def restaurar_gpos_padrao():
    """Remove as políticas locais e força a atualização."""
    caminhos_gpo = [
        os.path.join(os.environ['WINDIR'], 'System32', 'GroupPolicy'),
        os.path.join(os.environ['WINDIR'], 'System32', 'GroupPolicyUsers')
    ]
    for path in caminhos_gpo:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                yield f"Removido: {path}"
            except Exception as e:
                yield f"ERRO ao remover {path}: {e}"
    yield from executar_comando_cmd("gpupdate /force", timeout=300)
    yield "Restauração das GPOs padrão concluída."

def resetar_microsoft_store():
    """Limpa o cache e re-registra a Microsoft Store."""
    yield "Iniciando reset da Microsoft Store..."
    yield from executar_comando_cmd("wsreset.exe -q", timeout=120)
    yield "Comando de limpeza de cache enviado."
    yield "Re-registrando o aplicativo da Store..."
    comando = 'Get-AppxPackage *WindowsStore* -AllUsers | ForEach-Object {Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml"}'
    yield from executar_comando_powershell(comando)
    yield "Comando de re-registro enviado."

def ajustar_melhor_desempenho():
    """Habilitar a opção Ajustar para obter o melhor desempenho dentro de configurações avançadas e desativar serviços do Xbox."""
    yield "Iniciando ajuste para melhor desempenho..."
    comando = r"""Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" -Name VisualFXSetting -Value 2"""
    yield from executar_comando_powershell(comando)
    yield "Comando de melhorar desempenho enviado."
    yield "Confira nas configurações avançadas."
    yield from executar_comando_cmd(r"sysdm.cpl ,3", timeout=120)
    
    yield "Limpando o cache DNS."
    yield from executar_comando_cmd(r"ipconfig /flushdns", timeout=120)

    yield "Desativando tela de boas-vindas..."
    comandoDesativarBoasVindas = r"""Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" -Name SubscribedContent-310093Enabled -Value 0"""
    yield from executar_comando_powershell(comandoDesativarBoasVindas)

    yield "Desativando animações no menu Iniciar..."
    comando_menu = r"""Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" -Name TaskbarAnimations -Value 0"""
    yield from executar_comando_powershell(comando_menu)
    
    yield "Desativando transições de janelas..."
    comando_transicoes = r"""Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name WindowMetrics -Value "-15"
    Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name MinAnimate -Value 0"""
    yield from executar_comando_powershell(comando_transicoes)
    
    yield "Desativando efeitos de transparência..."
    comando_transparencia = r"""Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name EnableTransparency -Value 0"""
    yield from executar_comando_powershell(comando_transparencia)
    
    yield "Desativando notificações de dicas..."
    comando_dicas = r"""Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" -Name SoftLandingEnabled -Value 0
    Set-ItemProperty -Path "HKCU:\Software\Policies\Microsoft\Windows\CloudContent" -Name DisableTailoredExperiences -Value 1 -Force -ErrorAction SilentlyContinue"""
    yield from executar_comando_powershell(comando_dicas)
    
    yield "Ajustando prioridade de I/O do sistema..."
    comando_io = r"""Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\PriorityControl" -Name Win32PrioritySeparation -Value 24"""
    yield from executar_comando_powershell(comando_io)
    
    yield "Aumentando tamanho do cache de disco..."
    comando_cache = r"""Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" -Name MaxRawWorkItems -Value 512"""
    yield from executar_comando_powershell(comando_cache)
    
    yield "Desativando serviços do Xbox..."
    comandos_xbox = [
        r'Stop-Service -Name "XboxGipSvc" -Force',
        r'Stop-Service -Name "XboxNetApiSvc" -Force',
        r'Stop-Service -Name "XblAuthManager" -Force',
        r'Stop-Service -Name "XblGameSave" -Force',
        r'Set-Service -Name "XboxGipSvc" -StartupType Disabled',
        r'Set-Service -Name "XboxNetApiSvc" -StartupType Disabled',
        r'Set-Service -Name "XblAuthManager" -StartupType Disabled',
        r'Set-Service -Name "XblGameSave" -StartupType Disabled'
    ]
    for cmd in comandos_xbox:
        yield from executar_comando_powershell(cmd)

    yield "Serviços do Xbox desativados com sucesso."

    yield "Desativando serviços adicionais..."
    comandos_servicos = [
        r'Stop-Service -Name "WpcSvc" -Force',          # Controle dos Pais
        r'Stop-Service -Name "WpcMonSvc" -Force',       # Controle dos Pais depende da versão do windows
        r'Stop-Service -Name "DiagTrack" -Force',       # Telemetria
        r'Stop-Service -Name "DusmSvc" -Force',         # Experiências do Usuário Conectado
        r'Stop-Service -Name "GameInputSvc" -Force',    # GameInput
        r'Stop-Service -Name "ScPolicySvc" -Force',     # Política de Remoção de Cartão Inteligente
        r'Stop-Service -Name "WbioSrvc" -Force',        # Biometria
        r'Stop-Service -Name "BDESVC" -Force',          # BitLocker
        r'Stop-Service -Name "SCardSvr" -Force',        # Cartão Inteligente
        r'Stop-Service -Name "icssvc" -Force',          # Hotspot Móvel
        r'Stop-Service -Name "WerSvc" -Force',          # Relatórios de Erro
        r'Stop-Service -Name "SensorService" -Force',   # Sensor
        r'Stop-Service -Name "PhoneSvc" -Force',        # Telefonia
        r'Stop-Service -Name "SysMain" -Force',         # SysMain
        r'Set-Service -Name "WpcSvc" -StartupType Disabled',
        r'Set-Service -Name "WpcMonSvc" -StartupType Disabled',
        r'Set-Service -Name "DiagTrack" -StartupType Disabled',
        r'Set-Service -Name "DusmSvc" -StartupType Disabled',
        r'Set-Service -Name "GameInputSvc" -StartupType Disabled',
        r'Set-Service -Name "ScPolicySvc" -StartupType Disabled',
        r'Set-Service -Name "WbioSrvc" -StartupType Disabled',
        r'Set-Service -Name "BDESVC" -StartupType Disabled',
        r'Set-Service -Name "SCardSvr" -StartupType Disabled',
        r'Set-Service -Name "icssvc" -StartupType Disabled',
        r'Set-Service -Name "WerSvc" -StartupType Disabled',
        r'Set-Service -Name "SensorService" -StartupType Disabled',
        r'Set-Service -Name "PhoneSvc" -StartupType Disabled',
        r'Set-Service -Name "SysMain" -StartupType Disabled'
    ]
    for cmd in comandos_servicos:
        yield from executar_comando_powershell(cmd)

    yield "Todos os serviços adicionais foram desativados com sucesso."


def forcar_atualizacao_gpos():
    """Força a atualização das Políticas de Grupo (gpupdate)."""
    yield "Forçando atualização das Políticas de Grupo (GPOs)..."
    yield from executar_comando_cmd("gpupdate /force", timeout=300)
    yield "Tentativa de atualização de GPO concluída."

# CORRIGIDO: Usa um arquivo temporário para obter o nome de usuário com acentos.
def limpar_pastas_usuario():
    """Limpa as pastas Desktop e Downloads do usuário, lidando com acentos."""
    yield "Iniciando limpeza de pastas do usuário..."
    temp_file = os.path.join(os.environ['TEMP'], 'current_user.tmp')
    # Comando PowerShell para salvar o nome de usuário em um arquivo com codificação UTF-8
    comando_ps = f"(Get-CimInstance -ClassName Win32_ComputerSystem).Username | Out-File -FilePath '{temp_file}' -Encoding utf8 -NoNewline"
    
    try:
        # Executa o comando para criar o arquivo
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando_ps],
            check=True, capture_output=True
        )

        # Lê o nome do usuário do arquivo com a codificação correta
        if not os.path.exists(temp_file):
            yield "ERRO: Arquivo temporário de usuário não foi criado."
            return
            
        with open(temp_file, 'r', encoding='utf-8') as f:
            nome_usuario_completo = f.read().strip()

        if not nome_usuario_completo:
            yield "ERRO: Não foi possível determinar o usuário logado."
            return
        
        nome_usuario = nome_usuario_completo.split('\\')[-1]
        yield f"Usuário ativo encontrado: {nome_usuario}"

        caminho_base_usuario = os.path.join("C:\\Users", nome_usuario)
        pastas_para_limpar = {
            "Desktop": os.path.join(caminho_base_usuario, "Desktop"),
            "Downloads": os.path.join(caminho_base_usuario, "Downloads")
        }
        itens_a_preservar = ('.lnk', '.url', '.ini')

        for nome_pasta, caminho_pasta in pastas_para_limpar.items():
            yield f"--- Limpando a pasta {nome_pasta} ---"
            if not os.path.exists(caminho_pasta):
                yield f"AVISO: Pasta não encontrada: {caminho_pasta}"
                continue
            for item in os.listdir(caminho_pasta):
                caminho_completo = os.path.join(caminho_pasta, item)
                if nome_pasta == "Desktop" and item.lower().endswith(itens_a_preservar):
                    yield f"Preservando: {item}"
                    continue
                try:
                    if os.path.isfile(caminho_completo) or os.path.islink(caminho_completo):
                        os.unlink(caminho_completo)
                    elif os.path.isdir(caminho_completo):
                        shutil.rmtree(caminho_completo)
                    yield f"Item removido: {item}"
                except Exception as e:
                    yield f"ERRO ao remover '{item}': {e}"
            yield f"Limpeza da pasta {nome_pasta} concluída."

    except subprocess.CalledProcessError as e:
        yield f"ERRO CRÍTICO ao obter nome do usuário: {e}"
        if e.stderr:
            yield f"Detalhes do erro do PowerShell: {e.stderr.decode('utf-8', 'ignore')}"
    except Exception as e:
        yield f"ERRO CRÍTICO ao limpar pastas do usuário: {e}"
    finally:
        # Garante que o arquivo temporário seja sempre removido
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
def manutencao_preventiva_1_click(config):
    """Executa uma sequência de tarefas de manutenção preventiva."""
    yield "--- INICIANDO MANUTENÇÃO PREVENTIVA COMPLETA ---"
    yield "\nPASSO 1/10: Baixando recursos da FCT..."
    yield from baixar_recursos_necessarios(config['URL_REPOSITORIO_FCT'])
    yield "\nPASSO 2/10: Restaurando GPOs Padrão..."
    yield from restaurar_gpos_padrao()
    yield "\nPASSO 3/10: Forçando Atualização de GPOs..."
    yield from forcar_atualizacao_gpos()
    yield "\nPASSO 4/10: Limpeza Geral do Sistema..."
    yield from iniciar_limpeza_sistema(config['URL_BLEACHBIT'])
    yield "\nPASSO 5/10: Limpando pastas do Usuário..."
    yield from limpar_pastas_usuario()
    yield "\nPASSO 6/10: Aplicando Tema Visual da FCT..."
    yield from aplicar_tema_fct(config['CAMINHO_TEMA'])
    yield "\nPASSO 7/10: Aplicando GPOs da FCT..."
    yield from aplicar_gpos_fct(config['CAMINHO_BASE_GPO'])
    yield "\nPASSO 8/10: Forçando atualização de GPO novamente..."
    yield from forcar_atualizacao_gpos()
    yield "\nPASSO 9/10: Resetando a Microsoft Store..."
    yield from resetar_microsoft_store()
    yield "\nPASSO 10/10: Habilitando ajuste de desempenho..."
    yield from ajustar_melhor_desempenho()
    yield "\n--- MANUTENÇÃO PREVENTIVA CONCLUÍDA ---"
    yield "É recomendado reiniciar o computador para que todas as alterações tenham efeito."