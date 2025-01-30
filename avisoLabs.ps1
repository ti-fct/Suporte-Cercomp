#Requires -Version 5

<#
.SYNOPSIS
    Sistema de avisos para laboratórios - FCT/UFG
.DESCRIPTION
    Exibe informações institucionais e de segurança no canto superior direito
.NOTES
    Versão: 3.5
    Autor: Departamento de TI FCT/UFG
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Função para obter IP corrigida
function Get-IPv4Address {
    $interfaces = [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() | 
        Where-Object { 
            $_.OperationalStatus -eq 'Up' -and 
            $_.NetworkInterfaceType -eq 'Ethernet'
        }
    
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
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
Computador: $env:COMPUTERNAME
Endereço IP: $(Get-IPv4Address)

[REGRAS DE USO]
• Uso exclusivo para atividades acadêmicas
• Proibido alterar configurações do sistema
• Não desconectar cabos ou periféricos
• Proibido consumo de alimentos no laboratório

[PROCEDIMENTOS AO SAIR]
1. Encerre todos os aplicativos (Ctrl + Shift + Esc)
2. Faça logout de todas as contas
3. Remova dispositivos externos
4. Desligue a estação corretamente

[SUPORTE TÉCNICO]
• Sistema: $((Get-CimInstance Win32_OperatingSystem).Caption)
• Último boot: $((Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToString('dd/MM/yyyy HH:mm'))
• Chamados: chamado.ufg.br
"@

# Configurações de estilo
$font = New-Object Drawing.Font("Segoe UI", 11, [Drawing.FontStyle]::Regular)
$boldFont = New-Object Drawing.Font("Segoe UI", 13, [Drawing.FontStyle]::Bold)
$textColor = [System.Drawing.Color]::White
$shadowColor = [System.Drawing.Color]::FromArgb(30,30,30)
$shadowOffset = 2
$maxWidth = 500
$lineHeight = 24  # Aumentado para melhor espaçamento

try {
    $screenWidth = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width
} catch {
    $screenWidth = 1920
}

$positionX = $screenWidth - ($maxWidth + 40)

# Criação da janela com altura ajustada
$form = New-Object Windows.Forms.Form
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.BackColor = 'Magenta'
$form.TransparencyKey = $form.BackColor
$form.StartPosition = 'Manual'
$form.Location = New-Object Drawing.Point($positionX, 40)
$form.Size = New-Object Drawing.Size($maxWidth, 650)  # Altura aumentada
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

    # Corrigindo a divisão de linhas para considerar diferentes tipos de quebra de linha
    $sections = $message -split "\r?\n"
    
    foreach ($section in $sections) {
        if ($section -match "▔+") {
            $e.Graphics.DrawLine(
                [System.Drawing.Pens]::Gray,
                ($sender.Width - 400), ($yPos + 5),
                ($sender.Width - 20), ($yPos + 5)
            )
            $yPos += 15
            continue
        }

        # Adicionado suporte para [SUPORTE TÉCNICO] em negrito
        if ($section -match "LABORATÓRIO|REGRAS|PROCEDIMENTOS|SUPORTE") {
            $currentFont = $boldFont
        } else {
            $currentFont = $font
        }

        # Desenho da sombra
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
        
        # Desenho do texto principal
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
        
        $yPos += $lineHeight + 3  # Espaçamento ajustado
    }
})

$form.Controls.Add($label)

# Execução
if ([Environment]::UserInteractive) {
    [void]$form.ShowDialog()
}
