# -*- mode: python ; coding: utf-8 -*-
#
# 打包命令（在 Windows 上执行，或通过 GitHub Actions 自动构建）：
#   pyinstaller rollcall.spec
#
# 目标平台：Windows 10+，Python 3.12

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 打包图标和静态资源
        ('assets/icon.ico', 'assets'),
        # qdarktheme 的样式资源
        *collect_data_files('qdarktheme'),
        # matplotlib 的字体和样式数据
        *collect_data_files('matplotlib'),
    ],
    hiddenimports=[
        # matplotlib Qt5 后端
        'matplotlib.backends.backend_qt5agg',
        # PyQt5 核心模块
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        # openpyxl 需要的 lxml/et_xmlfile
        'openpyxl',
        *collect_submodules('openpyxl'),
        # matplotlib.colors 运行时依赖 Pillow
        'PIL',
        *collect_submodules('PIL'),
        # qdarktheme 内部动态导入
        *collect_submodules('qdarktheme'),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型库，减小体积
        'tkinter',
        'unittest',
        'email',
        'html',
        'http',
        'xmlrpc',
        'IPython',
        'jupyter',
        'notebook',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='随机点名',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,               # 启用 UPX 压缩（需安装 upx）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # 不显示命令行窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico', # 窗口和任务栏图标
    version_file=None,
)
