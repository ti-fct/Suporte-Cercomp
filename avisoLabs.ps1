#Requires -Version 5

<#
.SYNOPSIS
    Sistema de avisos para laboratórios - FCT/UFG
.DESCRIPTION
    Exibe informações institucionais e de segurança no canto superior direito
.NOTES
    Versão: 4.0
    Autor: Departamento de TI FCT/UFG (Diego)
#>


Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Get-LocalIP {
    try {
        $ip = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Ethernet*' -ErrorAction Stop | 
            Where-Object { $_.PrefixOrigin -ne 'WellKnown' }).IPAddress
        return ($ip -split '\n')[0]
    }
    catch {
        return "IP não detectado"
    }
}

$message = @"
LABORATÓRIO DE INFORMÁTICA - FCT/UFG
────────────────────────────────────
Computador: $env:COMPUTERNAME
IP Local: $(Get-LocalIP)

[REGRAS DE USO]
• Uso exclusivo para atividades acadêmicas
• Proibido alterar configurações do sistema
• Não consumir alimentos no labortatório

[PROCEDIMENTOS AO SAIR]
1. Encerre todos os aplicativos
2. Faça logout das contas
3. Remova dispositivos externos

[SUPORTE TÉCNICO]
Chamados: chamado.ufg.br
"@

# Configurações de estilo
$font = New-Object Drawing.Font("Segoe UI", 10, [Drawing.FontStyle]::Regular)
$boldFont = New-Object Drawing.Font("Segoe UI", 11, [Drawing.FontStyle]::Bold)
$textColor = [System.Drawing.Color]::White
$shadowColor = [System.Drawing.Color]::FromArgb(30, 30, 30)  # Cinza escuro
$shadowBrush = New-Object Drawing.SolidBrush($shadowColor)

# Configuração da janela
$form = New-Object Windows.Forms.Form
$form.FormBorderStyle = 'None'
$form.BackColor = 'Lime'  # Cor alterada para melhor transparência
$form.TransparencyKey = 'Lime'
$form.TopMost = $true
$form.ShowInTaskbar = $false  # Remove da barra de tarefas

# Cálculo de tamanho
$lineCount = ($message -split "\r?\n").Count
$form.Size = New-Object Drawing.Size(400, (40 + ($lineCount * 24)))

# Posicionamento
$screenWidth = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea.Width
$form.Location = New-Object Drawing.Point(($screenWidth - 420), 20)

$label = New-Object Windows.Forms.Label
$label.Size = $form.Size
$label.ForeColor = $textColor

$label.Add_Paint({
    param($sender, $e)
    
    $e.Graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $y = 10
    $format = New-Object Drawing.StringFormat
    $format.Alignment = [Drawing.StringAlignment]::Far
    
    foreach ($line in ($message -split "\r?\n")) {
        $currentFont = if ($line -match "LABORATÓRIO|\[.*\]") { $boldFont } else { $font }
        $posX = $sender.Width - 15
        
        # Sombra suave
        $e.Graphics.DrawString(
            $line,
            $currentFont,
            $shadowBrush,
            [Drawing.PointF]::new($posX - 1, $y + 1),
            $format
        )
        
        # Texto principal
        $e.Graphics.DrawString(
            $line,
            $currentFont,
            [Drawing.Brushes]::White,
            [Drawing.PointF]::new($posX, $y),
            $format
        )
        
        $y += 24
    }
})

$form.Controls.Add($label)
$form.ShowDialog()
