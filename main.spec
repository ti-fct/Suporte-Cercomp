# -*- mode: python ; coding: utf-8 -*-
import qtawesome
import os

# Encontra o caminho do qtawesome dinamicamente
qta_path = os.path.dirname(qtawesome.__file__)

block_cipher = None

a = Analysis(['main.py'],
             pathex=['C:\\dev\\fct-toolkit'], # Coloque o caminho do seu projeto aqui
             binaries=[],
             datas=[
                 ('logo.png', '.'), # Adiciona o logo.png
                 (qta_path, 'qtawesome') # Adiciona a pasta do qtawesome
             ],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Suporte-Cercomp-FCT',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False, # Alterado para False (sem console)
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='icon.ico',
          # Linha crucial para solicitar permissão de admin
          uac_admin=True)