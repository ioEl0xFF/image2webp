"""
ログユーティリティ
ログ設定と共通のログ処理機能を提供
"""

import os
import shutil
import logging
from typing import Optional
from pathlib import Path

from . import config


def setup_logging() -> logging.Logger:
    """
    ログ設定を初期化
    
    Returns:
        設定されたロガーインスタンス
    """
    # ログディレクトリを作成（既存の場合は削除）
    log_dir = Path(config.LOG_DIR)
    if log_dir.exists():
        shutil.rmtree(log_dir)
    log_dir.mkdir(exist_ok=True)

    # ログファイルのパス
    log_file_path = log_dir / config.LOG_FILE

    # ログ設定
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()  # コンソールにも出力
        ]
    )

    # ロガーを取得
    logger = logging.getLogger(__name__)
    logger.info("ログ設定を初期化しました")

    # 存在しない画像記録ファイルを初期化
    _initialize_missing_images_file(logger)

    return logger


def _initialize_missing_images_file(logger: logging.Logger) -> None:
    """
    存在しない画像記録ファイルを初期化
    
    Args:
        logger: ロガーインスタンス
    """
    missing_images_file = Path(config.LOG_DIR) / "missing_images.txt"
    try:
        with open(missing_images_file, "w", encoding="utf-8") as f:
            f.write("# 存在しない画像ファイル一覧\n")
            f.write("# 形式: DOCXファイル名: 画像名\n\n")
        logger.info("存在しない画像記録ファイルを初期化しました")
    except Exception as e:
        logger.error(f"存在しない画像記録ファイルの初期化に失敗: {e}")


def record_missing_image(image_name: str, docx_file_name: str, logger: logging.Logger) -> None:
    """
    存在しない画像名をファイルに記録
    
    Args:
        image_name: 存在しない画像名
        docx_file_name: DOCXファイル名（拡張子なし）
        logger: ロガーインスタンス
    """
    missing_images_file = Path(config.LOG_DIR) / "missing_images.txt"

    try:
        with open(missing_images_file, "a", encoding="utf-8") as f:
            f.write(f"{docx_file_name}: {image_name}\n")
        
        logger.info(f"存在しない画像を記録: {image_name} (ファイル: {docx_file_name})")
    except Exception as e:
        logger.error(f"存在しない画像の記録に失敗: {image_name} - {e}")


def get_missing_images_count() -> int:
    """
    存在しない画像ファイルの件数を取得
    
    Returns:
        存在しない画像ファイルの件数
    """
    missing_images_file = Path(config.LOG_DIR) / "missing_images.txt"
    
    if not missing_images_file.exists():
        return 0
    
    try:
        with open(missing_images_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # コメント行を除く
            return len([line for line in lines if not line.strip().startswith("#") and line.strip()])
    except Exception:
        return 0


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    ロガーインスタンスを取得
    
    Args:
        name: ロガー名（Noneの場合は呼び出し元のモジュール名を使用）
    
    Returns:
        ロガーインスタンス
    """
    return logging.getLogger(name or __name__)
