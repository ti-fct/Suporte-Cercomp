#Requires -Version 5

<#
.SYNOPSIS
    Overlay de avisos para laboratórios UFG
.DESCRIPTION
    Exibe mensagem não intrusiva no canto superior direito da tela
.NOTES
    Versão: 2.2
    Autor: Departamento de TI UFG
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Configurações do texto
$message = @"
[📜] LABS UFG
[🖥️] $env:COMPUTERNAME

[❗] ATENÇÃO: Mantenha o foco acadêmico!

[⚠️] ANTES DE SAIR:
① Encerre TODOS os aplicativos
② Deslogue de contas pessoais
③ Remova arquivos temporários
④ Feche todas as janelas

[🔒] Dados não salvos serão APAGADOS automaticamente!
"@

# Configurações adaptativas
$maxWidth = 480
$defaultScreenWidth = 1920

try {
    $screenWidth = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width
}
catch {
    $screenWidth = $defaultScreenWidth
}

$positionX = $screenWidth - ($maxWidth + 20)

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

# Configuração do texto
$label = New-Object Windows.Forms.Label
$label.Font = New-Object Drawing.Font("Segoe UI Emoji", 12, [Drawing.FontStyle]::Bold)
$label.ForeColor = [System.Drawing.Color]::White
$label.BackColor = [System.Drawing.Color]::Transparent
$label.Size = $form.Size
$label.TextAlign = [System.Drawing.ContentAlignment]::TopRight

# Desenho com borda
$label.Add_Paint({
    param($sender, $e)
    
    $format = New-Object Drawing.StringFormat
    $format.Alignment = [Drawing.StringAlignment]::Far
    
    # Sombra
    $e.Graphics.DrawString(
        $message,
        $label.Font,
        [System.Drawing.Brushes]::Black,
        (New-Object Drawing.RectangleF(2, 2, $sender.Width, $sender.Height)),
        $format
    )
    
    # Texto principal
    $e.Graphics.DrawString(
        $message,
        $label.Font,
        [System.Drawing.Brushes]::White,
        (New-Object Drawing.RectangleF(0, 0, $sender.Width, $sender.Height)),
        $format
    )
})

$form.Controls.Add($label)

# Execução
if ([Environment]::UserInteractive) {
    [void]$form.ShowDialog()
}
