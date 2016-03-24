# -*- mode: python -*-

block_cipher = None
options = [('v', None, 'OPTION'), ('W ignore', None, 'OPTION')]

add_datas = [
             ('shuoming','.'),
             ('arm-none-eabi-gdb.exe','.'),
             ('arm-none-eabi-nm.exe','.'),
             ('32x32.ico','.'),
             ]
a = Analysis(['parsemain.py'],
             pathex=['D:\\code\\dumparse_w'],
             binaries=None,
             datas=add_datas,
             hiddenimports=[],
             hookspath=['.'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          options,
          name='parsemain',
          debug=False,
          strip=False,
          upx=True,
          console=False ,icon='128x128.ico',version='version.txt')
          
#exe = EXE(pyz,
#          a.scripts,
#          options,
#          exclude_binaries=True,
#          name='parsemain',
#          debug=False,
#          strip=False,
#          upx=True,
#          console=True )
#coll = COLLECT(exe,
#               a.binaries,
#               a.zipfiles,
#               a.datas,
#               strip=False,
#               upx=True,
#               name='parsemain')
