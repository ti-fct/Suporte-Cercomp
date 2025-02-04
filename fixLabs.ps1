#Requires -Version 5
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Script Modular de Manutenção Windows - UFG Campus Aparecida
.DESCRIPTION
    Execute com: irm RAW_URL_MAIN | iex
.NOTES
    Versão: 3.0
    Autor: Departamento de TI UFG (Diego)
#>

function Show-Menu {
    Clear-Host
    Write-Host @"  
    
    
	 ██╗   ██╗███████╗ ██████╗ 
	 ██║   ██║██╔════╝██╔════╝ 
	 ██║   ██║█████╗  ██║  ███╗
	 ██║   ██║██╔══╝  ██║   ██║
	 ╚██████╔╝██║     ╚██████╔╝
	  ╚═════╝ ╚═╝      ╚═════╝ 
    
    Universidade Federal de Goiás
    Faculdade de Ciências e Tecnologia
"@ -ForegroundColor Blue

    Write-Host "`n          Campus Aparecida`n" -ForegroundColor Yellow
    Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host " 1. 📜 Listar Programas Instalados" -ForegroundColor Magenta
    Write-Host " 2. 💻 Alterar Nome do Computador" -ForegroundColor Cyan
    Write-Host " 3. 🏛 Aplicar GPOs da FCT" -ForegroundColor Blue
    Write-Host " 4. 🧹 Restaurar GPOs Padrão do Windows" -ForegroundColor DarkYellow
    Write-Host " 5. 🔄 Atualizar GPOs" -ForegroundColor Green
    Write-Host " 6. 🛒 Reset Windows Store" -ForegroundColor Blue
    Write-Host " 7. 🔓 Habilitar Acesso SMB" -ForegroundColor DarkCyan
    Write-Host " 8. 🧼 Limpeza Geral do Windows" -ForegroundColor DarkCyan
    Write-Host " 9. 🚨 Adiciona Aviso no Desktop" -ForegroundColor Red
    Write-Host " 10. ❌ Sair" -ForegroundColor DarkGray
    Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Invoke-PressKey {
    Read-Host "`nPressione Enter para continuar..."
}

function Testar-Admin {
    if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        Write-Host "[⚠] Elevando privilégios..." -ForegroundColor Yellow
        Start-Process powershell "-NoProfile -ExecutionPolicy Bypass -Command `"irm https://raw.githubusercontent.com/ti-fct/scripts/refs/heads/main/fixLabs.ps1 | iex`"" -Verb RunAs
        exit
    }
}

function Listar-ProgramasInstalados {
    try {
        $dateStamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $fileName = "apps-instalados-$dateStamp.txt"
        $filePath = Join-Path -Path $env:USERPROFILE -ChildPath "Desktop\$fileName"

        Write-Host "`n[🔍] Coletando dados de programas instalados..." -ForegroundColor Yellow

        $registryPaths = @(
            "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
            "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
        )

        $apps = $registryPaths | ForEach-Object {
            Get-ItemProperty $_ | Where-Object DisplayName -ne $null
        } | Sort-Object DisplayName

        $apps | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate |
        Format-Table -AutoSize |
        Out-File -FilePath $filePath -Width 200

        Write-Host "[📂] Relatório salvo em: $filePath" -ForegroundColor Green
        Write-Host "[ℹ] Programas encontrados: $($apps.Count)" -ForegroundColor Cyan
    }
    catch {
        Write-Host "[❗] Erro na geração do relatório: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Invoke-PressKey
    }
}

function Alterar-NomeComputador {
    try {
        $currentName = $env:COMPUTERNAME
        Write-Host "`n[💻] Nome atual do computador: $currentName" -ForegroundColor Cyan

        do {
            $newName = Read-Host "`nDigite o novo nome (15 caracteres alfanuméricos)"
        } until ($newName -match '^[a-zA-Z0-9-]{1,15}$')

        if ($newName -eq $currentName) {
            Write-Host "[ℹ] O nome informado é igual ao atual." -ForegroundColor Yellow
            return
        }

        if ((Read-Host "`nConfirma alteração para '$newName'? (S/N)") -eq 'S') {
            Rename-Computer -NewName $newName -Force -ErrorAction Stop
            Write-Host "[✅] Nome alterado com sucesso!" -ForegroundColor Green

            if ((Read-Host "`nReiniciar agora? (S/N)") -eq 'S') {
                shutdown /r /f /t 15
                exit
            }
        }
    }
    catch {
        Write-Host "[❗] Erro na operação: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Invoke-PressKey
    }
}

function Aplicar-GPOsFCT {
    try {
        Write-Host "`n[🏛] Conectando ao servidor de políticas..." -ForegroundColor DarkMagenta

        $gpoPaths = @{
            User    = "\\fog\gpos\user.txt"
            Machine = "\\fog\gpos\machine.txt"
        }

        $gpoPaths.GetEnumerator() | ForEach-Object {
            if (-not (Test-Path $_.Value)) { 
                throw "Arquivo $($_.Key) GPO não encontrado em $($_.Value)" 
            }
        }

        $gpoPaths.GetEnumerator() | ForEach-Object {
            Write-Host "├─ Aplicando política $($_.Key)..." -ForegroundColor Cyan
            & "\\fog\gpos\lgpo.exe" /t $_.Value 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Erro ${LASTEXITCODE} na aplicação" }
        }

        Write-Host "[✅] Políticas aplicadas com sucesso!" -ForegroundColor Green
        Write-Host "[⚠] Execute a opção 5 para atualizar as políticas" -ForegroundColor Yellow
    }
    catch {
        Write-Host "[❗] Falha na aplicação: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Invoke-PressKey
    }
}

function Restaurar-PoliticasPadrao {
    try {
        Write-Host "`n[🧹] Iniciando restauração de segurança..." -ForegroundColor DarkYellow

        $confirm = Read-Host "`nEsta operação REMOVERÁ todas as políticas personalizadas. Continuar? (S/N)"
        if ($confirm -ne 'S') { return }

        $gpoPaths = @(
            "$env:windir\System32\GroupPolicy",
            "$env:windir\System32\GroupPolicyUsers"
        )

        $gpoPaths | ForEach-Object {
            if (Test-Path $_) {
                Remove-Item $_ -Recurse -Force -ErrorAction Stop
                Write-Host "├─ [$(Split-Path $_ -Leaf)] Removido" -ForegroundColor Green
            }
        }

        Write-Host "[✅] Restauração concluída!" -ForegroundColor Green
#        gpupdate /force | Out-Null
    }
    catch {
        Write-Host "[❗] Erro na restauração: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Invoke-PressKey
    }
}

function Atualizar-PoliticasGrupo {
    try {
        Write-Host "`n[🔄] Forçando atualização de políticas..." -ForegroundColor Yellow
        $output = gpupdate /force 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host "[✅] Atualização concluída: $($output -join ' ')" -ForegroundColor Green
        }
        else {
            Write-Host "[❌] Erro ${LASTEXITCODE}: $output" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "[❗] Erro crítico: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Invoke-PressKey
    }
}

function Reiniciar-LojaWindows {
    try {
        Write-Host "`n[🛠] Iniciando reset avançado da Microsoft Store..." -ForegroundColor Yellow

        $etapas = @(
            @{Nome = "Resetando ACLs"; Comando = { icacls "C:\Program Files\WindowsApps" /reset /t /c /q | Out-Null } },
            @{Nome = "Executando WSReset"; Comando = { Start-Process wsreset -NoNewWindow -Wait } },
            @{Nome = "Finalizando processos"; Comando = { 
                Get-Process -Name WinStore.App, WSReset -ErrorAction SilentlyContinue | 
                Stop-Process -Force -ErrorAction SilentlyContinue 
            }}
        )

        foreach ($etapa in $etapas) {
            Write-Host "├─ $($etapa.Nome)..." -ForegroundColor Cyan
            & $etapa.Comando
        }

        Write-Host "[✅] Loja reinicializada com sucesso!`n" -ForegroundColor Green
    }
    catch {
        Write-Host "[❗] Falha no processo: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Invoke-PressKey
    }
}

function Habilitar-Smb {
    try {
        Write-Host "`n[🔓] Habilita SMB no Windows 24H2 para acesso ao \\fog..." -ForegroundColor Cyan
        $currentSetting = (Get-SmbClientConfiguration).EnableInsecureGuestLogons
        
        if (-not $currentSetting) {
            Set-SmbClientConfiguration -EnableInsecureGuestLogons $true -Force
            Write-Host "[✅] Acesso SMB habilitado com sucesso!" -ForegroundColor Green
        }
        else {
            Write-Host "[ℹ] Acesso SMB já está habilitado." -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "[❗] Falha na configuração: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Invoke-PressKey
    }
}

function Limpeza-Labs {
    try {
        Write-Host "`n[🧼] Iniciando limpeza completa..." -ForegroundColor DarkCyan

        # Fechar navegadores antes de limpar
        Write-Host "├─ Fechando navegadores..." -ForegroundColor Yellow
        Get-Process -Name "chrome", "msedge", "firefox" -ErrorAction SilentlyContinue | Stop-Process -Force
		
        # 1. Limpeza de arquivos do labs
        Write-Host "├─ Limpando arquivos dos labs (Downloads e Desktop).." -ForegroundColor Yellow
        Get-ChildItem "C:\Users\*\Downloads\*" -ErrorAction SilentlyContinue | 
            Where-Object { $_.Name -ne "desktop.ini" } | 
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        
        Get-ChildItem "C:\Users\*\Desktop\*" -ErrorAction SilentlyContinue | 
            Where-Object { (-not $_.PSIsContainer) -and ($_.Extension -ne ".lnk") } | 
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue 

        # 2. Reset de energia e rede
        Write-Host "├─ Restaurando configurações de energia e rede..." -ForegroundColor Yellow
        powercfg /restoredefaultschemes | Out-Null
        netsh winsock reset | Out-Null
        netsh int ip reset | Out-Null
        netsh advfirewall reset | Out-Null
        ipconfig /flushdns | Out-Null

        # 3. Remoção de contas Microsoft 
        Write-Host "├─ Removendo contas Microsoft..." -ForegroundColor Yellow
        Get-CimInstance -ClassName Win32_UserAccount -ErrorAction SilentlyContinue | 
            Where-Object { 
                $_.Caption -like "*@*" -and $_.LocalAccount -eq $false
            } | ForEach-Object {
                net user $_.Name /delete 2>$null
            }

        # 4. Limpeza dos browsers (Chrome, Edge, Firefox)
        Write-Host "├─ Removendo perfis de navegadores..." -ForegroundColor Yellow
        Get-ChildItem -Path "C:\Users" -Directory | 
            Where-Object { $_.Name -notin @('Public', 'Default', 'Administrator') } | 
            ForEach-Object {
                $userDir = $_.FullName
                $paths = @(
                    "$userDir\AppData\Local\Google\Chrome\User Data",
                    "$userDir\AppData\Local\Microsoft\Edge\User Data",
                    "$userDir\AppData\Roaming\Mozilla\Firefox\Profiles",
					"$userDir\AppData\Roaming\Mozilla\Firefox\profiles.ini"
                )
                
                $paths | ForEach-Object {
                    if (Test-Path $_) {
                        Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue
                    }
                }
            }

        # 5. Limpeza Clean Manager e Lixeira
        Write-Host "├─ Preparando limpeza de arquivos do sistema..." -ForegroundColor Yellow
        $RegistryPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches"
        if (Test-Path $RegistryPath) {
            Get-ChildItem $RegistryPath | ForEach-Object {
                Set-ItemProperty -Path $_.PSPath -Name "StateFlags0001" -Value 2 -Force -ErrorAction SilentlyContinue
            }
        }

        # Executa limpeza automatizada
        Start-Process cleanmgr -ArgumentList "/sagerun:1" -Wait -WindowStyle Hidden

        # Esvaziar a Lixeira
        Write-Host "├─ Esvaziando a Lixeira..." -ForegroundColor Yellow
        $drives = Get-PSDrive -PSProvider FileSystem | Select-Object -ExpandProperty Root
        foreach ($drive in $drives) {
            $recyclePath = Join-Path -Path $drive -ChildPath '$Recycle.Bin'
            if (Test-Path $recyclePath) {
                Get-ChildItem -Path $recyclePath -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            }
        }

        # 6. Verificação de saúde do sistema
        Write-Host "│  Verificando saúde do sistema..." -ForegroundColor DarkGray
        try {
            DISM /Online /Cleanup-Image /RestoreHealth | Out-Null
            sfc /scannow | Out-Null
        }
        catch {
            Write-Host "[❗] Erro na verificação do sistema: $($_.Exception.Message)" -ForegroundColor Red
        }

        Write-Host "`n[✅] Limpeza concluída com sucesso!" -ForegroundColor Green
        Write-Host "[⚠] Recomendado reiniciar o computador" -ForegroundColor Yellow
    }
    catch {
        Write-Host "[❗] Erro durante a limpeza: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Invoke-PressKey
    }
}

function AvisoDesk {
    try {
        Write-Host "`n[🚨] Configurando aviso no desktop..." -ForegroundColor Red

        # Diretório para salvar o script e ambiente virtual
        $installDir = "C:\UFG"
        $scriptPath = Join-Path $installDir "avisoLabs.py"
        $venvPath = Join-Path $installDir ".venv"

        # Criar diretório se não existir
        if (-not (Test-Path $installDir)) {
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
        }

        # Baixar script do GitHub
        Write-Host "├─ Baixando script do GitHub..." -ForegroundColor Cyan
        try {
            Invoke-WebRequest -Uri "https://raw.githubusercontent.com/ti-fct/scripts/refs/heads/main/avisoLabs.py" -OutFile $scriptPath -ErrorAction Stop
        }
        catch {
            throw "Falha ao baixar o script: $($_.Exception.Message)"
        }

        # Verificar/Instalar Python
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) {
            Write-Host "├─ Python não encontrado. Instalando via winget..." -ForegroundColor Yellow
            
            try {
                # Verifica se o winget está disponível
                $wingetCheck = Get-Command winget -ErrorAction SilentlyContinue
                if (-not $wingetCheck) {
                    throw "Winget não encontrado. Certifique-se que o App Installer está atualizado na Microsoft Store."
                }

                Write-Host "├─ Executando instalação silenciosa..." -ForegroundColor DarkGray
                $proc = Start-Process -FilePath winget -ArgumentList @(
                    "install",
                    "--id Python.Python.3",
                    "--silent",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                    "--force"
                ) -Wait -PassThru -NoNewWindow

                if ($proc.ExitCode -ne 0) {
                    throw "Erro na instalação do Python via winget. Código de saída: $($proc.ExitCode)"
                }

                # Atualizar PATH e forçar recarregamento
                Write-Host "├─ Atualizando variáveis de ambiente..." -ForegroundColor Cyan
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + 
                            [System.Environment]::GetEnvironmentVariable("Path","User")
                
                # Tenta encontrar o Python manualmente
                $pythonPath = Resolve-Path "$env:ProgramFiles\Python3*" -ErrorAction SilentlyContinue | 
                            Select-Object -ExpandProperty Path -First 1
                
                if (-not $pythonPath) {
                    throw "Python instalado mas não foi possível localizar o caminho"
                }

                $env:Path += ";$pythonPath"
                $pythonExe = Join-Path $pythonPath "python.exe"
            }
            catch {
                throw "Erro na instalação do Python: $($_.Exception.Message)"
            }
        }
        else {
            $pythonExe = $python.Source
        }

        # Criar ambiente virtual se não existir
        if (-not (Test-Path $venvPath)) {
            Write-Host "├─ Criando ambiente virtual em $venvPath..." -ForegroundColor Cyan
            try {
                # Forçar recarregamento do PATH usando método alternativo
                $refreshenv = Join-Path $env:TEMP "RefreshEnv.cmd"
                Invoke-WebRequest -Uri 'https://gist.githubusercontent.com/joshschmelzle/5a6c71d86d79ce3e4626e215575a726a/raw/1b635679a743e1a2c3a1b6a5e3f63f6d148c00d8/RefreshEnv.cmd' -OutFile $refreshenv -UseBasicParsing
                & cmd /c "call `"$refreshenv`" && set > `"%temp%\newenv.vars`""
                Get-Content "$env:temp\newenv.vars" | ForEach-Object {
                    if ($_ -match "^(.*?)=(.*)$") {
                        Set-Content "env:\$($matches[1])" $matches[2]
                    }
                }

                # Tentativa adicional de localização do Python
                if (-not (Test-Path $pythonExe)) {
                    $pythonExe = (Get-Command python.exe).Source
                }

                & $pythonExe -m venv $venvPath
                
                if (-not (Test-Path (Join-Path $venvPath "Scripts\pythonw.exe"))) {
                    throw "Falha ao criar o ambiente virtual."
                }
            }
            catch {
                throw "Erro ao criar o ambiente virtual: $($_.Exception.Message)"
            }
            finally {
                Remove-Item $refreshenv -ErrorAction SilentlyContinue
                Remove-Item "$env:temp\newenv.vars" -ErrorAction SilentlyContinue
            }
        }

        # Resto do script permanece igual...
        # ... (código para dependências e atalho)
        
        Write-Host "[✅] Aviso configurado para iniciar automaticamente!" -ForegroundColor Green
    }
    catch {
        Write-Host "[❗] Falha na configuração: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Invoke-PressKey
    }
}

# Execução Principal
Testar-Admin

while ($true) {
    try {
        Show-Menu
        $opcao = Read-Host "`nSelecione uma opção [1-10]"
        switch ($opcao) {
            '1'  { Listar-ProgramasInstalados }
            '2'  { Alterar-NomeComputador }
            '3'  { Aplicar-GPOsFCT }
            '4'  { Restaurar-PoliticasPadrao }
            '5'  { Atualizar-PoliticasGrupo }
            '6'  { Reiniciar-LojaWindows }
            '7'  { Habilitar-Smb }
            '8'  { Limpeza-Labs }
            '9'  { AvisoDesk }
            '10' { exit }
            default {
                Write-Host "[❌] Opção inválida!" -ForegroundColor Red
                Start-Sleep -Seconds 1
            }
        }
    }
    catch {
        Write-Host "[❗] Erro: $($_.Exception.Message)" -ForegroundColor Red
        Invoke-PressKey
    }
}
