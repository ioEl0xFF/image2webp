"""
img2webp.config - 設定管理モジュール

JSON設定ファイルの読み込み、デフォルト値の管理を行います。
"""

from .loader import config_loader

__all__ = ["config_loader"]
