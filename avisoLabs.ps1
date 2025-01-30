#Requires -Version 5

<#
.SYNOPSIS
    Sistema de avisos para laboratórios - FCT/UFG
.DESCRIPTION
    Exibe informações institucionais e de segurança no canto superior direito
.NOTES
    Versão: 3.2
    Autor: Departamento de TI FCT/UFG
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Função para obter IP
function Get-IPv4Address {
    $interfaces = [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() | 
        Where-Object { $_.OperationalStatus -eq 'Up' -and $_.NetworkInterfaceType -ne 'Loopback' }
    
    foreach ($interface in $interfaces) {
        $address = $interface.GetIPProperties().UnicastAddresses |
            Where-Object { $_.Address.AddressFamily -eq 'InterNetwork' }
        
        if ($address) {
            return $address.Address.ToString()
        }
    }
    return "IP não disponível"
}

# Configurações do texto
$message = @"
LABORATÓRIO DE INFORMÁTICA - FCT/UFG
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
Computador: $env:COMPUTERNAME
Endereço IP: $(Get-IPv4Address)

REGRAS DE USO:
• Uso exclusivo para atividades acadêmicas
• Proibido acesso a sites não educacionais
• Não salve arquivos localmente

PROCEDIMENTOS AO SAIR:
1. Encerre todos os aplicativos
2. Faça logout de todas as contas
3. Remova dispositivos USB
4. Desligue o computador

Problemas? 
Abra um chamado em: chamado.ufg.br
"@

# Configurações de estilo
$font = New-Object Drawing.Font("Segoe UI", 12, [Drawing.FontStyle]::Regular)
$boldFont = New-Object Drawing.Font("Segoe UI", 14, [Drawing.FontStyle]::Bold)
$textColor = [System.Drawing.Color]::White
$shadowColor = [System.Drawing.Color]::FromArgb(30,30,30) # Cinza escuro
$shadowOffset = 2
$maxWidth = 500
$lineHeight = 22

try {
    $screenWidth = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width
}
catch {
    $screenWidth = 1920
}

$positionX = $screenWidth - ($maxWidth + 40)

# Criação da janela
$form = New-Object Windows.Forms.Form
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.BackColor = 'Magenta'
$form.TransparencyKey = $form.BackColor
$form.StartPosition = 'Manual'
$form.Location = New-Object Drawing.Point($positionX, 40)
$form.Size = New-Object Drawing.Size($maxWidth, 480)
$form.TopMost = $false
$form.ShowInTaskbar = $false

# Controle personalizado
$label = New-Object Windows.Forms.Label
$label.Font = $font
$label.ForeColor = $textColor
$label.BackColor = [System.Drawing.Color]::Transparent
$label.Size = $form.Size
$label.TextAlign = [System.Drawing.ContentAlignment]::TopRight

# Desenho aprimorado
$label.Add_Paint({
    param($sender, $e)
    
    $format = New-Object Drawing.StringFormat
    $format.Alignment = [Drawing.StringAlignment]::Far
    $yPos = 10

    $sections = $message -split "`n"
    
    foreach ($section in $sections) {
        # Verificação de estilo condicional
        if ($section -match "▔") {
            $e.Graphics.DrawLine(
                [System.Drawing.Pens]::Gray,
                ($sender.Width - 400), ($yPos + 5),
                ($sender.Width - 20), ($yPos + 5)
            )
            $yPos += 15
            continue
        }

        # Lógica corrigida para versões antigas do PowerShell
        if ($section -match "LABORATÓRIO|REGRAS|PROCEDIMENTOS") {
            $currentFont = $boldFont
        } else {
            $currentFont = $font
        }

        # Sombra melhorada
        $e.Graphics.DrawString(
            $section,
            $currentFont,
            (New-Object Drawing.SolidBrush($shadowColor)),
            (New-Object Drawing.RectangleF(
                $shadowOffset,
                $yPos + $shadowOffset,
                $sender.Width - ($shadowOffset * 2),
                $lineHeight
            )),
            $format
        )
        
        # Texto principal
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

# Execução
if ([Environment]::UserInteractive) {
    [void]$form.ShowDialog()
}
