"""
img2webp - DOCXファイルから画像名を抽出し、WebP形式に変換するPythonツール

このパッケージは以下の機能を提供します：
- DOCXファイル内のテーブルから画像名を自動抽出
- 複数サイズのWebP画像を生成
- HTMLのメディアクエリに基づいた画像サイズの自動選択
- GUI版とCLI版の両方をサポート
"""

__version__ = "2.2.0"
__author__ = "img2webp Team"

# メインクラスをインポート
from .main import Img2WebpProcessor

__all__ = ["Img2WebpProcessor"]
