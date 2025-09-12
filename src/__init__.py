"""
img2webp パッケージ
DOCXファイルから画像名を抽出し、WebP形式に変換するPythonツール
"""

__version__ = "2.0.0"
__author__ = "img2webp"
__description__ = "DOCX画像名抽出・WebP変換ツール"

# メインクラスをパッケージレベルでインポート可能にする
from .main import Img2WebpProcessor

__all__ = [
    "Img2WebpProcessor",
]
