#Requires -Version 5

<#
.SYNOPSIS
    Sistema de avisos para laboratórios - FCT/UFG
.DESCRIPTION
    Exibe informações institucionais e de segurança no canto superior direito
.NOTES
    Versão: 4.0
    Autor: Departamento de TI FCT/UFG
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Função para obter IP Local melhorada
function Get-LocalIPv4 {
    try {
        $adapters = Get-NetAdapter -Physical | Where-Object Status -eq 'Up'
        foreach ($adapter in $adapters) {
            $ipv4 = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 | 
                    Where-Object PrefixOrigin -ne 'WellKnown' | 
                    Select-Object -ExpandProperty IPAddress -First 1
            if ($ipv4) { return $ipv4 }
        }
        return "Sem conexão"
    }
    catch { return "IP não disponível" }
}

# Configurações do texto
$message = @"
LABORATÓRIO DE INFORMÁTICA - FCT/UFG
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
Computador: $env:COMPUTERNAME
Endereço IP: $(Get-LocalIPv4)

[REGRAS DE USO]
• Uso exclusivo para atividades acadêmicas
• Proibido alterar configurações do sistema
• Não desconectar cabos ou periféricos

[PROCEDIMENTOS AO SAIR]
1. Encerre todos os aplicativos (Ctrl + Shift + Esc)
2. Faça logout de todas as contas
3. Remova dispositivos externos
4. Desligue a estação corretamente

[SUPORTE TÉCNICO]
• Sistema: $((Get-CimInstance Win32_OperatingSystem).Caption)
• Último boot: $((Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToString('dd/MM/yyyy HH:mm'))
• Chamados: chamados.fct.ufg.br | Ramal: 1234
"@

# Configurações de estilo aprimoradas
$font = New-Object Drawing.Font("Segoe UI", 11, [Drawing.FontStyle]::Regular)
$boldFont = New-Object Drawing.Font("Segoe UI", 13, [Drawing.FontStyle]::Bold)
$textColor = [System.Drawing.Color]::FromArgb(245,245,245) # Branco suave
$shadowColor = [System.Drawing.Color]::FromArgb(15,15,15)   # Preto fosco
$shadowOffset = 1.5
$maxWidth = 520
$lineHeight = 22
$opacity = 0.95 # 95% de opacidade

# Detecção automática de resolução
try {
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    $screenWidth = $screen.Bounds.Width
    $dpiScale = $screen.Bounds.Width/$screen.WorkingArea.Width
}
catch {
    $screenWidth = 1920
    $dpiScale = 1
}

$positionX = [math]::Round(($screenWidth/$dpiScale) - ($maxWidth + 40))

# Criação da janela com transparência real
$form = New-Object Windows.Forms.Form
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.BackColor = 'Magenta'
$form.TransparencyKey = $form.BackColor
$form.Opacity = $opacity
$form.StartPosition = 'Manual'
$form.Location = New-Object Drawing.Point($positionX, 40)
$form.Size = New-Object Drawing.Size($maxWidth, 520)
$form.TopMost = $false
$form.ShowInTaskbar = $false

# Renderização avançada
$label = New-Object Windows.Forms.Label
$label.Font = $font
$label.ForeColor = $textColor
$label.BackColor = [System.Drawing.Color]::Transparent
$label.Size = $form.Size
$label.TextAlign = [System.Drawing.ContentAlignment]::TopRight

$label.Add_Paint({
    param($sender, $e)
    
    $format = New-Object Drawing.StringFormat
    $format.Alignment = [Drawing.StringAlignment]::Far
    $yPos = 15
    $sectionPadding = 10

    $sections = $message -split "`n"
    
    foreach ($section in $sections) {
        if ($section -match "▔") {
            $e.Graphics.DrawLine(
                (New-Object Drawing.Pen([System.Drawing.Color]::Gray, 1.5)),
                ($sender.Width - 450), ($yPos + 3),
                ($sender.Width - 30), ($yPos + 3)
            )
            $yPos += 20
            continue
        }

        $currentFont = $font
        if ($section -match "\[.*\]") {
            $currentFont = $boldFont
            $section = $section -replace '[\[\]]',''
        }

        # Renderização com suavização
        $e.Graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
        
        # Sombra suave
        for ($i = 0; $i -lt 3; $i++) {
            $e.Graphics.DrawString(
                $section,
                $currentFont,
                [System.Drawing.Brushes]::Black,
                (New-Object Drawing.RectangleF(
                    ($shadowOffset + $i),
                    ($yPos + $shadowOffset + $i),
                    $sender.Width,
                    $lineHeight
                )),
                $format
            )
        }
        
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
        
        $yPos += $lineHeight + (($section -match '^$') ? 10 : 5)
    }
})

$form.Controls.Add($label)

# Execução segura
if ([Environment]::UserInteractive) {
    try { [void]$form.ShowDialog() }
    catch { Write-Warning "Erro gráfico: $($_.Exception.Message)" }
}
