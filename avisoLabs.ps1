#Requires -Version 5

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Função SIMPLIFICADA para IP
function Get-LocalIP {
    try {
        $ip = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Ethernet*' -ErrorAction Stop | 
            Where-Object {$_.PrefixOrigin -ne 'WellKnown'}).IPAddress
        return $ip
    }
    catch {
        return "IP não detectado"
    }
}

# Texto com formatação simplificada
$message = @"
LABORATÓRIO DE INFORMÁTICA - FCT/UFG
────────────────────────────────────
Computador: $env:COMPUTERNAME
IP Local: $(Get-LocalIP)

[REGRAS DE USO]
• Uso exclusivo para atividades acadêmicas
• Proibido alterar configurações do sistema

[PROCEDIMENTOS AO SAIR]
1. Encerre todos os aplicativos
2. Faça logout das contas
3. Remova dispositivos externos

[SUPORTE TÉCNICO]
Sistema: $((Get-CimInstance Win32_OperatingSystem).Caption)
Último boot: $((Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToString('dd/MM HH:mm'))
Chamados: chamado.ufg.br
"@

# Configurações de estilo
$font = New-Object Drawing.Font("Segoe UI", 10, [Drawing.FontStyle]::Regular)
$boldFont = New-Object Drawing.Font("Segoe UI", 11, [Drawing.FontStyle]::Bold)
$textColor = [System.Drawing.Color]::White
$shadowColor = [System.Drawing.Color]::Black

# Cálculo dinâmico do tamanho
$lineCount = ($message -split "\r?\n").Count
$formHeight = 40 + ($lineCount * 24)

$form = New-Object Windows.Forms.Form
$form.FormBorderStyle = 'None'
$form.BackColor = 'Magenta'
$form.TransparencyKey = 'Magenta'
$form.TopMost = $true
$form.Size = New-Object Drawing.Size(400, $formHeight)
$form.StartPosition = 'Manual'
$form.Location = New-Object Drawing.Point(
    [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea.Width - 420,
    20
)

$label = New-Object Windows.Forms.Label
$label.Font = $font
$label.ForeColor = $textColor
$label.Size = $form.Size
$label.TextAlign = 'TopRight'

$label.Add_Paint({
    param($sender, $e)
    
    $y = 10
    $lines = $message -split "\r?\n"
    
    foreach ($line in $lines) {
        $currentFont = if ($line -match "LABORATÓRIO|\[.*\]") { $boldFont } else { $font }
        
        # Sombra
        $e.Graphics.DrawString(
            $line,
            $currentFont,
            $shadowColor,
            [Drawing.Rectangle]::FromLTRB(2, $y + 2, $sender.Width - 5, $sender.Height),
            (New-Object Drawing.StringFormat([Drawing.StringFormatFlags]::NoWrap))
        )
        
        # Texto
        $e.Graphics.DrawString(
            $line,
            $currentFont,
            [Drawing.Brushes]::White,
            [Drawing.Rectangle]::FromLTRB(0, $y, $sender.Width - 5, $sender.Height),
            (New-Object Drawing.StringFormat([Drawing.StringFormatFlags]::NoWrap))
        )
        
        $y += 24
    }
})

$form.Controls.Add($label)
$form.ShowDialog()
