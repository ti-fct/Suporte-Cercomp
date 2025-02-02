#Requires -Version 5
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Sistema de avisos para laboratórios - FCT/UFG
.DESCRIPTION
    Exibe informações institucionais e de segurança no canto superior direito
.NOTES
    Versão: 6
    Autor: Departamento de TI FCT/UFG
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Função otimizada para obter IP
function Get-LocalIP {
    try {
        return (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Ethernet*' -ErrorAction Stop | 
            Where-Object { $_.PrefixOrigin -ne 'WellKnown' } | Select-Object -First 1).IPAddress
    }
    catch {
        return "IP não detectado"
    }
}

# Configurações do texto
$message = @"
LABORATÓRIO DE INFORMÁTICA - FCT/UFG
────────────────────────────────────
Computador: $env:COMPUTERNAME
IP Local: $(Get-LocalIP)

[REGRAS DE USO]
• Uso exclusivo para atividades acadêmicas
• Não alterar configurações do sistema
• Não consumir alimentos no laboratório

[PROCEDIMENTOS AO SAIR]
1. Encerre todos os aplicativos
2. Faça logout das contas
3. Remova dispositivos externos

[SUPORTE TÉCNICO]
chamado.ufg.br
"@

# Configurações de estilo
$font = New-Object Drawing.Font("Segoe UI", 11, [Drawing.FontStyle]::Regular)
$boldFont = New-Object Drawing.Font("Segoe UI", 13, [Drawing.FontStyle]::Bold)
$textColor = [System.Drawing.Color]::White
$shadowColor = [System.Drawing.Color]::FromArgb(255, 30, 30, 30)
$shadowOffset = 3
$maxWidth = 500
$lineHeight = 22

# Posicionamento dinâmico
try {
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    $positionX = $screen.Bounds.Width - ($maxWidth + 40)
    $positionY = 40
}
catch {
    $positionX = 1400
    $positionY = 40
}

# Criação da janela
$form = New-Object Windows.Forms.Form
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.BackColor = 'Black'
$form.TransparencyKey = $form.BackColor
$form.StartPosition = 'Manual'
$form.Location = New-Object Drawing.Point($positionX, $positionY)
$form.Size = New-Object Drawing.Size($maxWidth, 480)
$form.TopMost = $true
$form.ShowInTaskbar = $false

# Controle personalizado
$label = New-Object Windows.Forms.Label
$label.Font = $font
$label.ForeColor = $textColor
$label.BackColor = [System.Drawing.Color]::Transparent
$label.Size = $form.Size
$label.TextAlign = [System.Drawing.ContentAlignment]::TopRight

# Desenho otimizado
$label.Add_Paint({
    param($sender, $e)
    
    $format = New-Object Drawing.StringFormat
    $format.Alignment = [Drawing.StringAlignment]::Far
    $yPos = 10

    $sections = $message -split "`n"
    
    foreach ($section in $sections) {
        if ($section -match "▔") {
            $e.Graphics.DrawLine(
                [System.Drawing.Pens]::Gray,
                ($sender.Width - 400), ($yPos + 5),
                ($sender.Width - 20), ($yPos + 5)
            )
            $yPos += 15
            continue
        }

        $currentFont = if ($section -match "LABORATÓRIO|REGRAS|PROCEDIMENTOS") { $boldFont } else { $font }

        # Sombra
        $e.Graphics.DrawString(
            $section,
            $currentFont,
            (New-Object Drawing.SolidBrush($shadowColor)),
            (New-Object Drawing.RectangleF(
                $shadowOffset,
                $yPos + $shadowOffset,
                $sender.Width - $shadowOffset,
                $lineHeight
            )),
            $format
        )
        
        # Texto
        $e.Graphics.DrawString(
            $section,
            $currentFont,
            (New-Object Drawing.SolidBrush($textColor)),
            (New-Object Drawing.RectangleF(
                0,
                $yPos,
                $sender.Width,
                $lineHeight
            )),
            $format
        )
        
        $yPos += $lineHeight + 5
    }
})

$form.Controls.Add($label)

# Execução persistente
[void]$form.ShowDialog()
