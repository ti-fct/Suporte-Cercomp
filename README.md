# Script Modular de Manutenção Windows - UFG Campus Aparecida

Este é um script PowerShell desenvolvido pelo Departamento de TI da Universidade Federal de Goiás (UFG), Campus Aparecida, para facilitar a manutenção e administração de sistemas Windows. O script oferece uma variedade de funcionalidades que podem ser executadas por administradores de sistema para gerenciar computadores em um ambiente de laboratório ou corporativo.

## Funcionalidades Principais

O script oferece as seguintes funcionalidades:

1. **📜 Listar Programas Instalados**: Gera um relatório de todos os programas instalados no computador e salva o resultado em um arquivo de texto.
2. **💻 Alterar Nome do Computador**: Permite alterar o nome do computador, com validação de entrada e opção de reinicialização.
3. **🏛 Aplicar GPOs da FCT**: Aplica políticas de grupo (GPOs) específicas da Faculdade de Ciências e Tecnologia (FCT) a partir de um servidor de políticas.
4. **🧹 Restaurar GPOs Padrão do Windows**: Remove todas as políticas de grupo personalizadas e restaura as configurações padrão do Windows.
5. **🔄 Atualizar GPOs**: Força a atualização das políticas de grupo após aplicar ou restaurar as GPOs.
6. **🛒 Reset Windows Store**: Reinicializa a Microsoft Store, útil após a aplicação de GPOs que afetam a loja.
7. **🧼 Labs Limpeza Geral do Windows (Beta)**: Executa uma limpeza completa do sistema, incluindo:
   - Limpeza de arquivos temporários e pastas de usuários (Downloads e Desktop).
   - Reset de configurações de energia e rede.
   - Remoção de contas Microsoft.
   - Restauração de temas visuais.
   - Limpeza avançada com BleachBit.
   - Verificação de saúde do sistema com DISM e SFC.
8. **🚀 Reiniciar Computador**: Reinicia o computador após confirmação do usuário.
9. **❌ Sair do Script**: Encerra a execução do script.

## Como Utilizar

### Pré-requisitos

- **PowerShell 5.0 ou superior**: O script requer PowerShell versão 5.0 ou superior.
- **Privilégios de Administrador**: O script deve ser executado com privilégios de administrador.

### Execução

1. **Baixar o Script**: O script pode ser baixado diretamente do repositório GitHub.
2. **Executar o Script**: Execute o script com o seguinte comando no PowerShell:

   ```powershell
   irm https://raw.githubusercontent.com/ti-fct/scripts/refs/heads/main/fct.ps1 | iex
   ```

   ```powershell
   Set-SmbClientConfiguration -EnableInsecureGuestLogons $true
   ```
