#!/usr/bin/env python3
"""
GUI版のテスト用スクリプト
基本的な動作確認を行う
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# srcディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def create_test_environment():
    """テスト環境を作成"""
    print("テスト環境を作成中...")
    
    # テスト用ディレクトリ構造を作成
    test_dirs = ['test_docxs', 'test_images', 'test_html', 'test_output']
    
    for dir_name in test_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"作成: {dir_name}/")
    
    # テスト用DOCXファイルの内容を作成（実際のDOCXファイルは手動で配置が必要）
    docx_readme = """# テスト用DOCXファイル配置場所

このディレクトリに、テスト用のDOCXファイルを配置してください。

## DOCXファイルの要件

テーブル内に以下の形式で画像名を記述してください：

| コード | 画像名 |
|--------|--------|
| COMFRPTC09 | ＜画像＞sample-image-01 |
| GSTFRPTA15 | ＜画像名＞sample-image-02 |

## 対応パターン

- `＜画像＞image-name-01`
- `＜画像名＞image-name-02`
- `＜画像1＞image-name-03`
- `画像名：image-name-04` (全角コロン)
- `画像名:image-name-05` (半角コロン)
"""
    
    with open('test_docxs/README.txt', 'w', encoding='utf-8') as f:
        f.write(docx_readme)
    
    # テスト用画像ディレクトリのREADME
    images_readme = """# テスト用画像ファイル配置場所

このディレクトリに、テスト用の画像ファイルを配置してください。

## 対応形式

- JPG/JPEG
- PNG  
- WebP

## ファイル名例

- sample-image-01.jpg
- sample-image-02.png
- sample-image-03.webp

DOCXファイルで指定された画像名と一致するファイルを配置してください。
"""
    
    with open('test_images/README.txt', 'w', encoding='utf-8') as f:
        f.write(images_readme)
    
    # テスト用HTMLディレクトリのREADME
    html_readme = """# テスト用HTMLファイル配置場所

このディレクトリに、画像名置換対象のHTMLファイルを配置してください。

## ファイル名

DOCXファイル名と同じ名前のHTMLファイルを配置してください。

例：
- test.docx → test.html
- sample.docx → sample.html

## HTML内容例

```html
<source media="(min-width: 1562px)" data-srcset="sample-image-01.jpg">
<img data-src="sample-image-01.jpg" alt="サンプル画像">
```

このような画像参照がWebP形式に置換されます。
"""
    
    with open('test_html/README.txt', 'w', encoding='utf-8') as f:
        f.write(html_readme)
    
    print("✅ テスト環境の作成が完了しました")
    print("\n📁 作成されたディレクトリ:")
    for dir_name in test_dirs:
        print(f"  - {dir_name}/")
    
    print("\n📝 次の手順:")
    print("1. test_docxs/ にテスト用DOCXファイルを配置")
    print("2. test_images/ にテスト用画像ファイルを配置")
    print("3. test_html/ にテスト用HTMLファイルを配置（オプション）")
    print("4. python gui_main.py でGUIアプリを起動")
    print("5. 各ディレクトリを設定して変換テスト")


def check_dependencies():
    """依存関係をチェック"""
    print("依存関係をチェック中...")
    
    required_packages = {
        'tkinter': 'Tkinter (GUI)',
        'docx': 'python-docx (DOCXファイル処理)',
        'PIL': 'Pillow (画像処理)',
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - インストールが必要")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  不足パッケージ: {', '.join(missing_packages)}")
        print("以下のコマンドでインストールしてください:")
        if 'docx' in missing_packages:
            print("  pip install python-docx")
        if 'PIL' in missing_packages:
            print("  pip install Pillow")
        return False
    else:
        print("\n✅ すべての依存関係が満たされています")
        return True


def check_source_files():
    """ソースファイルの存在確認"""
    print("ソースファイルをチェック中...")
    
    required_files = [
        'gui_main.py',
        'src/__init__.py',
        'src/main.py',
        'src/config.py',
        'src/gui_processor.py',
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - ファイルが見つかりません")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  不足ファイル: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ すべての必要ファイルが存在します")
        return True


def run_basic_import_test():
    """基本的なインポートテスト"""
    print("基本的なインポートテストを実行中...")
    
    try:
        # GUI関連のインポート
        import tkinter as tk
        from tkinter import ttk
        print("✅ Tkinter インポート成功")
        
        # カスタムモジュールのインポート
        from src.gui_processor import GuiImg2WebpProcessor, ProcessorThread
        print("✅ GUI processor インポート成功")
        
        from src.config import WEBP_QUALITY, WIDTH_MAP
        print("✅ Config インポート成功")
        
        print("\n✅ すべてのインポートが成功しました")
        return True
        
    except ImportError as e:
        print(f"\n❌ インポートエラー: {e}")
        return False


def create_sample_files():
    """サンプルファイルを作成"""
    print("サンプルファイルを作成中...")
    
    # サンプル画像（1x1ピクセルの小さなPNG）を作成
    try:
        from PIL import Image
        
        # 小さなサンプル画像を作成
        sample_images = ['sample-image-01.png', 'sample-image-02.png']
        
        for img_name in sample_images:
            img_path = f'test_images/{img_name}'
            if not os.path.exists(img_path):
                # 100x100の白い画像を作成
                img = Image.new('RGB', (100, 100), color='white')
                img.save(img_path)
                print(f"✅ サンプル画像作成: {img_name}")
        
        print("✅ サンプル画像の作成が完了しました")
        
    except ImportError:
        print("⚠️  Pillowがインストールされていないため、サンプル画像は作成されませんでした")
    except Exception as e:
        print(f"⚠️  サンプル画像作成エラー: {e}")


def main():
    """メイン処理"""
    print("=== img2webp GUI版 テストスクリプト ===\n")
    
    # 1. 依存関係チェック
    if not check_dependencies():
        print("\n❌ 依存関係が不足しています。インストール後に再実行してください。")
        return False
    
    # 2. ソースファイルチェック
    if not check_source_files():
        print("\n❌ 必要なソースファイルが不足しています。")
        return False
    
    # 3. インポートテスト
    if not run_basic_import_test():
        print("\n❌ インポートテストに失敗しました。")
        return False
    
    # 4. テスト環境作成
    create_test_environment()
    
    # 5. サンプルファイル作成
    create_sample_files()
    
    print("\n" + "="*50)
    print("🎉 テスト準備が完了しました！")
    print("\n🚀 次のステップ:")
    print("1. 必要に応じてテスト用ファイルを追加配置")
    print("2. python gui_main.py でGUIを起動")
    print("3. テストディレクトリを指定して動作確認")
    print("\n💡 ヒント:")
    print("- GUIで各ディレクトリを test_xxx に設定")
    print("- WebP品質は 80-90 程度で十分")
    print("- ログエリアで処理状況を確認")
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ テスト準備に失敗しました。")
    
    input("\nEnterキーを押して終了...")
