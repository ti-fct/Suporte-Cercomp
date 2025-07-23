ATUALIZAR DOCUMENTAÇÃO

pip install pyinstaller PyQt6 qtawesome requests


pyinstaller --noconsole --onefile --name "ManutencaoUFG_GUI" --icon="seu_icone.ico" --add-data "C:/caminho/para/seu/.venv/Lib/site-packages/qtawesome;qtawesome" --add-data "logo.png;." ManutencaoUFG_GUI.py

