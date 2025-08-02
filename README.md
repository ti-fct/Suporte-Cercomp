# 🛠️ Ferramenta de Manutenção FCT/UFG

![PyQt6](https://img.shields.io/badge/framework-PyQt6-blue)
![plataforma](https://img.shields.io/badge/plataforma-Windows-lightgrey)

Ferramenta de manutenção desenvolvida para os laboratórios de informática da FCT/UFG. Automatiza tarefas administrativas em máquinas Windows, com foco em padronização, segurança e agilidade na gestão.

---

## 📁 Estrutura de Diretórios

```
├── backend.py             # Lógica e automações de manutenção
├── interface_grafica.py   # Interface gráfica (PyQt6)
└── main.py                # Inicializador principal da aplicação
```

---

## ⚙️ Funcionalidades

- ✅ Renomear o computador
- 🎨 Aplicar tema visual padrão da FCT
- 🏛️ Aplicar GPOs institucionais
- 🔄 Restaurar GPOs para o padrão do Windows
- 🧼 Limpeza do sistema com BleachBit
- 🛍️ Reset da Microsoft Store
- 📺 Gerenciar widget de aviso na área de trabalho (com regras de uso e suporte)
- ⚙️ Tela de configurações (caminhos de rede, URL de ferramentas etc.)
- ℹ️ Tela "Sobre" com versão e logo institucional

---

## 🐍 Requisitos

- Python **3.10+**
- Sistema Operacional: **Windows 10 ou 11**
- Permissões de **administrador**
- Acesso à internet

### 📦 Dependências Python

```bash
pip install PyQt6 qtawesome requests
```

---

## ▶️ Executando o Sistema (modo script)

1. Certifique-se de estar executando como **administrador**
2. Execute o `main.py`:

```bash
python main.py
```

---

## 🏗️ Como Gerar um Executável `.exe` (com PyInstaller)

### 1. Instale o PyInstaller

```bash
pip install pyinstaller
```

### 2. Gere o executável

```bash
pyinstaller main.py --name "Suporte-Cercomp-FCT" --onefile --noconsole --icon=assets/icone.ico --add-data="assets;assets" --hidden-import=qtawesome
```

- `--onefile`: gera um único `.exe`
- `--noconsole`: oculta o terminal (para aplicações GUI)
- `--icon=assets/icone.ico`: define o ícone (caminho atualizado)
- `--add-data="assets;assets"`: **ESSENCIAL**. Inclui todos os arquivos da pasta `assets` (como o `logo.png`) no executável.
- `--hidden-import=qtawesome`: necessário para importar corretamente os ícones da biblioteca.

### 3. Arquivos gerados:

- O executável estará em: `dist/Suporte-Cercomp-FCT.exe`
- As pastas `build/` e o arquivo `.spec` podem ser descartados após a compilação.

---

> Desenvolvido por TI – FCT/UFG