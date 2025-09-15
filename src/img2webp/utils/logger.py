"""
ログユーティリティ
ログ設定と共通のログ処理機能を提供
"""

import os
import shutil
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
from pathlib import Path
import time
import glob

from ..config import defaults as config


def setup_logging() -> logging.Logger:
    """
    ログ設定を初期化

    Returns:
        設定されたロガーインスタンス
    """
    # ログディレクトリを作成
    log_dir = Path(config.LOG_DIR)
    _ensure_log_directory(log_dir)

    # ログファイルのパス
    log_file_path = log_dir / config.LOG_FILE

    # 既存のハンドラーをクリア（重複を防ぐため）
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # ローテーションファイルハンドラーを作成
    # デフォルト: 最大10MB、5つのバックアップファイルを保持
    max_bytes = config.LOG_MAX_BYTES
    backup_count = config.LOG_BACKUP_COUNT
    
    file_handler = RotatingFileHandler(
        log_file_path, 
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # ログ設定
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        handlers=[
            file_handler,  # ローテーション対応ファイルハンドラー
            logging.StreamHandler()  # コンソールにも出力
        ],
        force=True  # 既存の設定を強制的に上書き
    )

    # ロガーを取得
    logger = logging.getLogger(__name__)
    logger.info("ログ設定を初期化しました")

    # 存在しない画像記録ファイルを初期化
    _initialize_missing_images_file(logger)
    
    # 古いログファイルをクリーンアップ
    _cleanup_old_logs(logger)

    return logger


def _ensure_log_directory(log_dir: Path) -> None:
    """
    ログディレクトリを安全に作成

    Args:
        log_dir: ログディレクトリのパス
    """
    try:
        # ディレクトリが存在しない場合は作成
        log_dir.mkdir(exist_ok=True)

        # 既存のログファイルがある場合、アクセス可能かチェック
        log_file_path = log_dir / config.LOG_FILE
        if log_file_path.exists():
            try:
                # ファイルが書き込み可能かテスト
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    pass  # 単純にファイルを開いて閉じる
            except (PermissionError, OSError) as e:
                # アクセスできない場合は一意な名前でバックアップ
                import time
                timestamp = int(time.time())
                backup_name = f"{config.LOG_FILE}.backup_{timestamp}"
                backup_path = log_dir / backup_name

                try:
                    log_file_path.rename(backup_path)
                    print(f"既存のログファイルを {backup_name} にバックアップしました")
                except OSError:
                    # バックアップも失敗した場合は新しい名前でログファイルを作成
                    import uuid
                    unique_suffix = str(uuid.uuid4())[:8]
                    config.LOG_FILE = f"LOG_{unique_suffix}.log"
                    print(f"ログファイル名を {config.LOG_FILE} に変更しました")

    except Exception as e:
        print(f"ログディレクトリの作成に失敗: {e}")
        # フォールバック: 現在のディレクトリに作成
        import tempfile
        log_dir = Path(tempfile.gettempdir()) / "img2webp_logs"
        log_dir.mkdir(exist_ok=True)
        print(f"フォールバック: ログディレクトリを {log_dir} に作成しました")


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


def _cleanup_old_logs(logger: logging.Logger) -> None:
    """
    古いログファイルをクリーンアップ
    
    Args:
        logger: ロガーインスタンス
    """
    try:
        log_dir = Path(config.LOG_DIR)
        if not log_dir.exists():
            return
            
        # 30日以上古いログファイルを削除
        cutoff_time = time.time() - (30 * 24 * 60 * 60)  # 30日前
        
        # ログファイルのパターンを検索
        log_patterns = [
            f"{config.LOG_FILE}.*",  # ローテーションされたファイル
            "*.log.backup_*",        # バックアップファイル
            "LOG_*.log"              # 一意名ファイル
        ]
        
        deleted_count = 0
        for pattern in log_patterns:
            for log_file in glob.glob(str(log_dir / pattern)):
                log_path = Path(log_file)
                try:
                    if log_path.stat().st_mtime < cutoff_time:
                        log_path.unlink()
                        deleted_count += 1
                        logger.info(f"古いログファイルを削除: {log_path.name}")
                except (OSError, FileNotFoundError):
                    # ファイルが既に削除されているか、アクセスできない場合
                    pass
        
        if deleted_count > 0:
            logger.info(f"古いログファイルを{deleted_count}個削除しました")
            
    except Exception as e:
        logger.warning(f"ログファイルクリーンアップ中にエラー: {e}")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    ロガーインスタンスを取得

    Args:
        name: ロガー名（Noneの場合は呼び出し元のモジュール名を使用）

    Returns:
        ロガーインスタンス
    """
    return logging.getLogger(name or __name__)
