#!/usr/bin/env python3
"""
img2webp CLI エントリーポイント
DOCXファイルから画像名を抽出し、WebP形式に変換する
"""

import sys
import os

# srcディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from img2webp.cli import main

if __name__ == "__main__":
    main()