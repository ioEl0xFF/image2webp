#!/usr/bin/env python3
"""
img2webp GUI版のexe化スクリプト
PyInstallerを使用してWindows実行ファイルを作成
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_dirs():
    """ビルドディレクトリをクリーンアップ"""
    dirs_to_clean = ['build', 'dist', '__pycache__']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"クリーンアップ中: {dir_name}")
            shutil.rmtree(dir_name)

    # .spec ファイルも削除
    for spec_file in Path('.').glob('*.spec'):
        print(f"削除中: {spec_file}")
        spec_file.unlink()


def create_pyinstaller_spec():
    """PyInstaller用の.specファイルを作成"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# データファイルとフォルダ
datas = [
    ('src', 'src'),
]

# 隠されたインポート
hiddenimports = [
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    'queue',
    'threading',
    'json',
    'pathlib',
    'docx',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
]

a = Analysis(
    ['gui_main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='img2webp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUIアプリケーションなのでコンソールを非表示
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
)
'''

    with open('img2webp.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("PyInstaller .specファイルを作成しました: img2webp.spec")


def create_version_info():
    """バージョン情報ファイルを作成"""
    version_info = '''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
# filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
# Set not needed items to zero 0.
filevers=(2,0,0,0),
prodvers=(2,0,0,0),
# Contains a bitmask that specifies the valid bits 'flags'r
mask=0x3f,
# Contains a bitmask that specifies the Boolean attributes of the file.
flags=0x0,
# The operating system for which this file was designed.
# 0x4 - NT and there is no need to change it.
OS=0x4,
# The general type of file.
# 0x1 - the file is an application.
fileType=0x1,
# The function of the file.
# 0x0 - the function is not defined for this fileType
subtype=0x0,
# Creation date and time stamp.
date=(0, 0)
),
  kids=[
StringFileInfo(
  [
  StringTable(
    u'041104B0',
    [StringStruct(u'CompanyName', u'img2webp'),
    StringStruct(u'FileDescription', u'DOCX画像名抽出・WebP変換ツール'),
    StringStruct(u'FileVersion', u'2.0.0.0'),
    StringStruct(u'InternalName', u'img2webp'),
    StringStruct(u'LegalCopyright', u'Copyright © 2024'),
    StringStruct(u'OriginalFilename', u'img2webp.exe'),
    StringStruct(u'ProductName', u'img2webp'),
    StringStruct(u'ProductVersion', u'2.0.0.0')])
  ]),
VarFileInfo([VarStruct(u'Translation', [1041, 1200])])
  ]
)
'''

    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)

    print("バージョン情報ファイルを作成しました: version_info.txt")


def create_requirements_for_build():
    """ビルド用のrequirements.txtを作成"""
    requirements = '''# img2webp GUI版のビルド用依存関係
python-docx>=0.8.11
Pillow>=8.0.0
pyinstaller>=5.0.0
'''

    with open('requirements_build.txt', 'w', encoding='utf-8') as f:
        f.write(requirements)

    print("ビルド用requirements.txtを作成しました: requirements_build.txt")


def install_build_dependencies():
    """ビルド用の依存関係をインストール"""
    print("ビルド用依存関係をインストール中...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_build.txt'],
                      check=True)
        print("依存関係のインストールが完了しました")
    except subprocess.CalledProcessError as e:
        print(f"依存関係のインストールに失敗しました: {e}")
        return False
    return True


def build_executable():
    """実行ファイルをビルド"""
    print("実行ファイルをビルド中...")
    try:
        subprocess.run([sys.executable, '-m', 'PyInstaller', 'img2webp.spec'],
                      check=True)
        print("ビルドが完了しました")

        # ビルド結果の確認（プラットフォームに応じて実行ファイル名を判定）
        import platform
        if platform.system() == "Windows":
            exe_path = Path('dist/img2webp.exe')
        else:
            exe_path = Path('dist/img2webp')

        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"実行ファイルが作成されました: {exe_path} ({size_mb:.1f} MB)")
            return True
        else:
            print("実行ファイルの作成に失敗しました")
            return False
    except subprocess.CalledProcessError as e:
        print(f"ビルドに失敗しました: {e}")
        return False


def create_distribution_package():
    """配布用パッケージを作成"""
    print("配布用パッケージを作成中...")

    # 配布用ディレクトリを作成
    dist_dir = Path('img2webp_distribution')
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()

    # 実行ファイルをコピー（プラットフォームに応じて実行ファイル名を判定）
    import platform
    if platform.system() == "Windows":
        exe_src = Path('dist/img2webp.exe')
        exe_dst = dist_dir / 'img2webp.exe'
    else:
        exe_src = Path('dist/img2webp')
        exe_dst = dist_dir / 'img2webp'

    if exe_src.exists():
        shutil.copy2(exe_src, exe_dst)

    # サンプルディレクトリ構造を作成
    sample_dirs = ['docxs', 'images', 'html', 'output']
    for dir_name in sample_dirs:
        (dist_dir / dir_name).mkdir()

    # README_GUI.mdを作成
    readme_content = '''# img2webp GUI版

## 使用方法

1. `img2webp.exe`を実行してください
2. 各ディレクトリを設定してください：
   - **DOCXファイル**: 処理対象のDOCXファイルが入っているディレクトリ
   - **画像ファイル**: 元画像ファイルが入っているディレクトリ
   - **HTMLファイル**: HTML置換対象ファイルが入っているディレクトリ（オプション）
   - **出力先**: 変換後のWebP画像を保存するディレクトリ
3. 必要に応じてWebP品質を調整してください（1-100）
4. 「変換開始」ボタンをクリックして処理を開始してください

## ディレクトリ構造例

```
img2webp_distribution/
├── img2webp.exe        # メインプログラム
├── docxs/              # DOCXファイル配置用
├── images/             # 元画像ファイル配置用
├── html/               # HTMLファイル配置用（オプション）
├── output/             # 変換後画像出力用
└── README_GUI.md       # このファイル
```

## 注意事項

- 初回実行時は、Windowsのセキュリティ警告が表示される場合があります
- 大量の画像を処理する場合は時間がかかります
- 処理中はログエリアで進捗を確認できます
- エラーが発生した場合は、ログエリアでエラー内容を確認してください

## トラブルシューティング

- **実行ファイルが起動しない**: Windows Defender等のセキュリティソフトが実行を阻止している可能性があります
- **処理が終わらない**: 大きなファイルや大量のファイルを処理している場合は時間がかかります
- **エラーが発生する**: ログエリアのエラーメッセージを確認し、ファイルパスや権限を確認してください
'''

    with open(dist_dir / 'README_GUI.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"配布用パッケージを作成しました: {dist_dir}")


def main():
    """メイン処理"""
    print("=== img2webp GUI版 exe化スクリプト ===")

    # 1. クリーンアップ
    print("\n1. ビルドディレクトリのクリーンアップ")
    clean_build_dirs()

    # 2. 必要なファイルを作成
    print("\n2. 設定ファイルの作成")
    create_pyinstaller_spec()
    create_version_info()
    create_requirements_for_build()

    # 3. 依存関係のインストール
    print("\n3. 依存関係のインストール")
    if not install_build_dependencies():
        print("依存関係のインストールに失敗したため、処理を中断します")
        return False

    # 4. 実行ファイルのビルド
    print("\n4. 実行ファイルのビルド")
    if not build_executable():
        print("ビルドに失敗しました")
        return False

    # 5. 配布用パッケージの作成
    print("\n5. 配布用パッケージの作成")
    create_distribution_package()

    print("\n=== ビルド完了 ===")
    import platform
    if platform.system() == "Windows":
        print("配布用ファイル: img2webp_distribution/img2webp.exe")
    else:
        print("配布用ファイル: img2webp_distribution/img2webp")
    print("配布用フォルダ: img2webp_distribution/")

    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ ビルドが成功しました！")
    else:
        print("\n❌ ビルドに失敗しました。")

    input("\nEnterキーを押して終了...")
