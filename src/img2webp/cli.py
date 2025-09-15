#!/usr/bin/env python3
"""
img2webp CLIエントリーポイント
DOCXファイルから画像名を抽出し、WebP形式に変換する
"""

from .main import Img2WebpProcessor


def main():
    """メイン関数"""
    processor = Img2WebpProcessor()
    processor.run()


if __name__ == "__main__":
    main()
