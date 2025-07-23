# Ferramenta de Manutenção FCT/UFG (Python Edition)

![versão](https://img.shields.io/badge/versão-5.1-blue)
![licença](https://img.shields.io/badge/licença-MIT-green)
![plataforma](https://img.shields.io/badge/plataforma-Windows-informational)

Ferramenta de manutenção e automação para estações de trabalho Windows, desenvolvida para os laboratórios da Faculdade de Ciências e Tecnologia (FCT) da Universidade Federal de Goiás (UFG). O script foi reescrito em Python para maior portabilidade e facilidade de distribuição.

---

## ✨ Funcionalidades Principais

- 💻 **Gerenciamento do Sistema**: Altere o nome do computador de forma rápida e segura.  
- 🏛️ **Políticas de Grupo (GPO)**: Aplique, remova e atualize GPOs personalizadas da instituição.  
- 🛒 **Reparo de Aplicativos**: Resete a Microsoft Store para corrigir problemas de funcionamento.  
- 🌐 **Conectividade**: Habilite o acesso a compartilhamentos de rede legados (SMBv1) para compatibilidade.  
- 🧼 **Limpeza Profunda**: Execute uma limpeza completa do sistema (temporários, lixeira, caches) com o BleachBit automatizado.  
- 🚨 **Aviso no Desktop**: Adicione um widget fixo com regras do laboratório.  
- 📄 **Logging Automático**: Todas as operações são registradas em `C:\UFG_Manutencao\script.log`.

---

## 📸 Screenshot

> Aqui está uma prévia da ferramenta em ação:

<!-- Substitua o link abaixo pela imagem real -->
`![Screenshot](https://link-da-sua-imagem.com)`

---

## 📋 Requisitos

### Para Usuários Finais
- Windows 10 ou 11  
- Acesso de Administrador

### Para Desenvolvedores
- Python 3.8+  
- pip (gerenciador de pacotes do Python)  
- Repositório clonado e dependências instaladas  

---

## 🚀 Instalação e Uso

### ✅ Opção 1: Usando o Executável (Recomendado)

1. Vá para a seção **Releases** deste repositório.  
2. Baixe o arquivo `ManutencaoUFG.exe`.  
3. Clique com o botão direito e selecione **"Executar como administrador"**.  
4. O menu principal será exibido.  

### ⚙️ Opção 2: Rodando a partir do Código-Fonte

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio

# Crie e ative um ambiente virtual
python -m venv .venv
.\.venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Execute como administrador
python ManutencaoUFG.py
```

> **Nota**: Certifique-se de que `requirements.txt` inclua `requests` e `PyQt5` ou instale-os manualmente:
```bash
pip install requests PyQt5
```

---

## 🛠️ Como Compilar seu Próprio Executável

Se você alterou o código-fonte e deseja gerar um `.exe`:

```bash
# Instale o PyInstaller
pip install pyinstaller

# Compile com elevação de privilégios
pyinstaller --onefile --uac-admin --name "ManutencaoUFG" ManutencaoUFG.py
```

- `--onefile`: Gera um único arquivo `.exe`  
- `--uac-admin`: Solicita execução como administrador  
- `--name`: Define o nome do executável  

> O executável será criado na pasta `dist`.

---

## 📁 Logging

Todas as ações são registradas em:

```
C:\UFG_Manutencao\script.log
```

Esse arquivo é essencial para diagnóstico de problemas.

---

## 🤝 Contribuição

Contribuições são bem-vindas!

1. Faça um **Fork** do projeto.  
2. Crie uma branch: `git checkout -b feature/sua-feature`  
3. Commit: `git commit -m 'Adiciona nova feature'`  
4. Push: `git push origin feature/sua-feature`  
5. Abra um **Pull Request**

Também é possível abrir uma **Issue** para relatar bugs ou sugerir melhorias.

---

## 📄 Licença

Distribuído sob a [Licença MIT](LICENSE).
