ATUALIZAR DOCUMENTAÇÃO

pip install pyinstaller PyQt6 qtawesome requests

pyinstaller --noconfirm main.py



pyinstaller --noconsole --name "ManutencaoFCT" --icon="favicon.ico" --add-data "C:/dev/FCT-Toolkit/venv/Lib/site-packages/qtawesome;qtawesome" main.py

