#Requires -Version 5
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Script Modular de Manutenção Windows - UFG Campus Aparecida
.DESCRIPTION
    Execute com: irm RAW_URL_MAIN | iex
.NOTES
    Versão: 3.1
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
    Write-Host " 5. 🔄 Atualizar GPOs (Usar após aplicar ou restaurar as GPOs)" -ForegroundColor Green
    Write-Host " 6. 🛒 Reset Windows Store" -ForegroundColor Blue
    Write-Host " 7. 🔓 Habilitar Acesso SMB no Win11 24H2" -ForegroundColor DarkCyan
    Write-Host " 8. 🧼 Labs Limpeza Geral do Windows (Beta)" -ForegroundColor DarkCyan
    Write-Host " 9. 🚀 Reiniciar Computador" -ForegroundColor Red
    Write-Host " 10. ❌ Sair do Script" -ForegroundColor DarkGray
    Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Invoke-PressKey {
    Read-Host "`nPressione Enter para continuar..."
}

function Testar-Admin {
    if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        Write-Host "[⚠] Elevando privilégios..." -ForegroundColor Yellow
        Start-Process powershell "-NoProfile -ExecutionPolicy Bypass -Command `"irm RAW_URL_MAIN | iex`"" -Verb RunAs
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
        gpupdate /force | Out-Null
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
        Write-Host "`n[🧼] Iniciando limpeza completa do Windows e usuários..." -ForegroundColor DarkCyan

        # 1. Limpeza de arquivos dos usuários
        Write-Host "├─ Limpando arquivos dos labs..." -ForegroundColor Yellow
        $pathsToClean = @(
            "C:\Users\*\Downloads\*",
            "C:\Users\*\Desktop\*"
        )
        
        $pathsToClean | ForEach-Object {
            Get-ChildItem $_ -ErrorAction SilentlyContinue | 
            Where-Object { $_.Name -ne "desktop.ini" -and (-not $_.PSIsContainer) } | 
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        }

        # 2. Reset de configurações de sistema
        Write-Host "├─ Restaurando configurações de rede e energia..." -ForegroundColor Yellow
        $commands = @(
            "powercfg /restoredefaultschemes",
            "netsh winsock reset",
            "netsh int ip reset",
            "netsh advfirewall reset",
            "ipconfig /flushdns"
        )
        $commands | ForEach-Object { Invoke-Expression $_ | Out-Null }

        # 3. Remoção de contas Microsoft
        Write-Host "├─ Removendo contas Microsoft..." -ForegroundColor Yellow
        Get-CimInstance -ClassName Win32_UserAccount -ErrorAction SilentlyContinue | 
        Where-Object { $_.Caption -like "*@*" -and -not $_.LocalAccount } | 
        ForEach-Object { net user $_.Name /delete 2>$null }

        # 4. Limpeza dos Browsers

# Finaliza processo dos navegadores

# Caminhos dos perfis dos navegadores

# Função para remover diretório se existir

# Resetando os navegadores


        # 5. Limpeza do sistema
        Write-Host "├─ Executando limpeza final..." -ForegroundColor Yellow
		# Defina o caminho correto do registro
$RegistryPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches"

# Para cada chave em VolumeCaches, configure a propriedade que habilita a opção de limpeza
Get-ChildItem -Path $RegistryPath | ForEach-Object { 
    Set-ItemProperty -Path $_.PSPath -Name StateFlags001 -Value 2 
}

        Start-Process -FilePath cleanmgr -ArgumentList "/sagerun:1" -Wait -WindowStyle Hidden

        # 6. Verificação de integridade
        Write-Host "├─ Verificando saúde do sistema..." -ForegroundColor Cyan
        try {
            DISM /Online /Cleanup-Image /RestoreHealth | Out-Null
            sfc /scannow | Out-Null
        }
        catch {
            Write-Host "[❗] Erro na verificação do sistema: $($_.Exception.Message)" -ForegroundColor Red
        }

        Write-Host "`n[✅] Limpeza concluída com sucesso!" -ForegroundColor Green
        if ((Read-Host "`nDeseja reiniciar o computador agora? (S/N)") -eq 'S') {
            shutdown /r /f /t 15
        }
    }
    catch {
        Write-Host "[❗] Erro durante a limpeza: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        Invoke-PressKey
    }
}

function Reiniciar-Computador {
    try {
        Write-Host "`n[🚨] ATENÇÃO: Operação irreversível!" -ForegroundColor Red
        $confirmacao = Read-Host "`nCONFIRME com 'REINICIAR' para prosseguir"
        if ($confirmacao -eq 'REINICIAR') {
            Write-Host "[⏳] Reinício em 15 segundos..." -ForegroundColor Yellow
            shutdown /r /f /t 15
            exit
        }
        else {
            Write-Host "[❌] Operação cancelada" -ForegroundColor Red
        }
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
        switch (Read-Host "`nSelecione uma opção [1-10]") {
            '1'  { Listar-ProgramasInstalados }
            '2'  { Alterar-NomeComputador }
            '3'  { Aplicar-GPOsFCT }
            '4'  { Restaurar-PoliticasPadrao }
            '5'  { Atualizar-PoliticasGrupo }
            '6'  { Reiniciar-LojaWindows }
            '7'  { Habilitar-Smb }
            '8'  { Limpeza-Labs }
            '9'  { Reiniciar-Computador }
            '10' { exit }
            default {
                Write-Host "[❌] Opção inválida!" -ForegroundColor Red
                Start-Sleep -Seconds 1
            }
        }
    }
    catch {
        Write-Host "[❗] Erro não tratado: $($_.Exception.Message)" -ForegroundColor Red
        Invoke-PressKey
    }
}
