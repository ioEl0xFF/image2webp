#!/usr/bin/env python3
"""
img2webp メインエントリーポイント
DOCXファイルから画像名を抽出し、WebP形式に変換する
"""

import sys
import os

# srcディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import Img2WebpProcessor


def main():
    """メイン関数"""
    processor = Img2WebpProcessor()
    processor.run()


if __name__ == "__main__":
    main()
