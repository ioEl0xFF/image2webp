#!/usr/bin/env python3
"""
img2webp GUI版のexe化スクリプト
PyInstallerを使用してWindows実行ファイルを作成
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path


def clean_build_dirs():
    """ビルドディレクトリをクリーンアップ"""
    # プロジェクトルートに移動
    os.chdir(Path(__file__).parent.parent.parent)

    dirs_to_clean = ['build/temp', 'build/dist', '__pycache__']

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
    ('src/img2webp', 'img2webp'),
    ('config/config.json', 'config'),
    ('config/gui_settings.json', 'config'),
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
    'img2webp',
    'img2webp.gui',
    'img2webp.core',
    'img2webp.config',
    'img2webp.utils',
]

a = Analysis(
    ['gui.py'],
    pathex=['src'],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''

    with open('img2webp.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("img2webp.spec ファイルを作成しました")


def build_exe():
    """PyInstallerでexeファイルを作成"""
    print("PyInstallerでexeファイルを作成中...")

    try:
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            'img2webp.spec',
            '--clean',
            '--noconfirm'
        ], check=True, capture_output=True, text=True)

        print("ビルドが完了しました！")
        print(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"ビルドエラー: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

    return True


def create_distribution_config():
    """配布用のconfig.jsonを作成"""
    print("配布用config.jsonを作成中...")

    # 元のconfig.jsonを読み込み
    source_config_path = Path("config/config.json")
    if not source_config_path.exists():
        print("警告: config/config.jsonが見つかりません")
        return False

    try:
        with open(source_config_path, 'r', encoding='utf-8') as f:
            source_config = json.load(f)

        # 配布用のdirectoriesセクションを定義
        dist_directories = {
            "docx_directory": "data/input/docx",
            "output_base_dir": "data/output",
            "images_dir": "data/input/images",
            "html_dir": "data/input/html",
            "log_dir": ".logs"
        }

        # 元の設定をコピーして、directoriesだけ置き換え
        dist_config = source_config.copy()
        dist_config["directories"] = dist_directories

        # 配布用ディレクトリにconfig.jsonを保存
        dist_config_path = Path("build/dist/config.json")
        dist_config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(dist_config_path, 'w', encoding='utf-8') as f:
            json.dump(dist_config, f, indent=2, ensure_ascii=False)

        print(f"配布用config.jsonを作成しました: {dist_config_path}")
        return True

    except Exception as e:
        print(f"config.json作成エラー: {e}")
        return False


def create_distribution():
    """配布用ディレクトリを作成"""
    print("配布用ディレクトリを作成中...")

    dist_dir = Path("build/dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    dist_dir.mkdir(parents=True, exist_ok=True)

    # 実行ファイルをコピー
    exe_source = Path("dist/img2webp.exe")
    if exe_source.exists():
        shutil.copy2(exe_source, dist_dir)
        print(f"実行ファイルをコピーしました: {dist_dir}/img2webp.exe")
    else:
        print("警告: 実行ファイルが見つかりません")
        return False

    # サンプルデータをコピー
    sample_dirs = ["data/samples/docx", "data/samples/images", "data/samples/html"]
    for sample_dir in sample_dirs:
        if Path(sample_dir).exists():
            dest_dir = dist_dir / sample_dir
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(sample_dir, dest_dir, dirs_exist_ok=True)

    # 入力用ディレクトリを作成
    input_dirs = ["data/input/docx", "data/input/images", "data/input/html", "data/output"]
    for input_dir in input_dirs:
        (dist_dir / input_dir).mkdir(parents=True, exist_ok=True)

    # READMEをコピー
    readme_files = ["README.md", "docs/GUI_GUIDE.md"]
    for readme in readme_files:
        if Path(readme).exists():
            shutil.copy2(readme, dist_dir)

    print(f"配布用ディレクトリが完成しました: {dist_dir}")
    return True


def main():
    """メイン実行関数"""
    print("=== img2webp exe化スクリプト ===")

    # 必要なパッケージのチェック
    try:
        import PyInstaller
        print(f"PyInstaller バージョン: {PyInstaller.__version__}")
    except ImportError:
        print("エラー: PyInstallerがインストールされていません")
        print("pip install pyinstaller でインストールしてください")
        sys.exit(1)

    # プロジェクトルートに移動
    original_dir = Path.cwd()
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)

    try:
        # 1. クリーンアップ
        print("1. ビルドディレクトリをクリーンアップ中...")
        clean_build_dirs()

        # 2. .specファイル作成
        print("2. PyInstaller設定ファイルを作成中...")
        create_pyinstaller_spec()

        # 3. exe作成
        print("3. 実行ファイルを作成中...")
        if not build_exe():
            print("ビルドに失敗しました")
            sys.exit(1)

        # 4. 配布用ディレクトリ作成
        print("4. 配布用パッケージを作成中...")
        if not create_distribution():
            print("配布用パッケージの作成に失敗しました")
            sys.exit(1)

        # 5. 配布用config.json作成
        print("5. 配布用config.jsonを作成中...")
        if not create_distribution_config():
            print("配布用config.jsonの作成に失敗しました")
            sys.exit(1)

        print("\n=== ビルド完了 ===")
        print(f"実行ファイル: {project_root}/build/dist/img2webp.exe")
        print("配布用ファイルも同じディレクトリに含まれています")
        print("config.jsonは元の設定から'directories'以外をコピーしました")

    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    main()