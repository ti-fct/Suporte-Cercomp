#Requires -Version 5
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Mensagem de aviso wallpaper labs UFG
.DESCRIPTION
    Overlay transparente com avisos institucionais
.NOTES
    Versão: 2.1
    Autor: Departamento de TI UFG (Diego)
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Configurações do texto
$message = @"
[📜] LABS UFG
[🖥️] $env:COMPUTERNAME

[❗] ATENÇÃO: Respeite as regras do laboratório

[⚠️] ANTES DE SAIR:
① Encerre TODOS os aplicativos
② Deslogue de contas (e-mail, redes sociais)
③ Remova arquivos pessoais
④ Feche todas as janelas

[🔒] DADOS NÃO SALVOS SERÃO PERDIDOS!
"@

# Configurações de estilo
$font = New-Object Drawing.Font("Segoe UI Emoji, Segoe UI", 12, [Drawing.FontStyle]::Bold)
$textColor = [System.Drawing.Color]::White
$shadowColor = [System.Drawing.Color]::Black
$shadowOffset = 2
$maxWidth = 480
$positionX = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width - ($maxWidth + 20)

# Criação da janela
$form = New-Object Windows.Forms.Form
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.BackColor = 'Magenta'
$form.TransparencyKey = $form.BackColor
$form.StartPosition = 'Manual'
$form.Location = New-Object Drawing.Point($positionX, 40)
$form.Size = New-Object Drawing.Size($maxWidth, 400)
$form.TopMost = $false
$form.ShowInTaskbar = $false

# Controle personalizado para texto
$label = New-Object Windows.Forms.Label
$label.Font = $font
$label.ForeColor = $textColor
$label.BackColor = [System.Drawing.Color]::Transparent
$label.Size = New-Object Drawing.Size($maxWidth, 380)
$label.TextAlign = [System.Drawing.ContentAlignment]::TopRight

# Desenho do texto com borda
$label.Add_Paint({
    param($sender, $e)
    
    $format = New-Object Drawing.StringFormat
    $format.Alignment = [Drawing.StringAlignment]::Far
    
    # Borda
    $rectShadow = New-Object Drawing.RectangleF(
        $shadowOffset,
        $shadowOffset,
        $sender.Width - ($shadowOffset * 2),
        $sender.Height - ($shadowOffset * 2)
    )
    $e.Graphics.DrawString($message, $font, (New-Object Drawing.SolidBrush($shadowColor)), $rectShadow, $format)
    
    # Texto principal
    $rectMain = New-Object Drawing.RectangleF(0, 0, $sender.Width, $sender.Height)
    $e.Graphics.DrawString($message, $font, (New-Object Drawing.SolidBrush($textColor)), $rectMain, $format)
})

$form.Controls.Add($label)

# Configurações de encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'

# Execução silenciosa
$form.ShowDialog() | Out-Null
