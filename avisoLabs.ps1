#Requires -Version 5

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
$shadowColor = [System.Drawing.Color]::FromArgb(30, 30, 30)
$shadowBrush = New-Object Drawing.SolidBrush($shadowColor)

# Configuração da janela
$form = New-Object Windows.Forms.Form
$form.FormBorderStyle = 'None'
$form.BackColor = [System.Drawing.Color]::FromArgb(0, 1, 0)
$form.TransparencyKey = $form.BackColor
$form.TopMost = $false  # Alterado para não ficar sobre outras janelas
$form.ShowInTaskbar = $false
$form.StartPosition = 'Manual'

# Cálculo de tamanho
$lineCount = ($message -split "\r?\n").Count
$formWidth = 400
$formHeight = 20 + ($lineCount * 24)
$form.Size = New-Object Drawing.Size($formWidth, $formHeight)

# Posicionamento no canto superior direito
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$form.Location = New-Object Drawing.Point(
    $screen.Width - $formWidth - 20,  # 20px da borda direita
    20  # 20px do topo
)

$label = New-Object Windows.Forms.Label
$label.Size = $form.Size

$label.Add_Paint({
    param($sender, $e)
    
    $e.Graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
    $y = 10
    $format = New-Object Drawing.StringFormat
    $format.Alignment = [Drawing.StringAlignment]::Far
    
    foreach ($line in ($message -split "\r?\n")) {
        $currentFont = if ($line -match "LABORATÓRIO|\[.*\]") { $boldFont } else { $font }
        $posX = $sender.Width - 20
        
        # Sombra
        $e.Graphics.DrawString(
            $line,
            $currentFont,
            $shadowBrush,
            [Drawing.PointF]::new($posX - 1, $y + 1),
            $format
        )
        
        # Texto
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
