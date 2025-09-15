"""
JSON設定ファイルローダー
config.jsonから設定を読み込み、アプリケーション全体で使用する設定値を管理
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Union, Optional, TypedDict
from dataclasses import dataclass, asdict
import logging


@dataclass
class DirectoryConfig:
    """ディレクトリ設定"""
    docx_directory: str = "data/input/docx"
    output_base_dir: str = "data/output"
    images_dir: str = "data/input/images"
    html_dir: str = "data/input/html"
    log_dir: str = ".logs"


@dataclass
class ImageProcessingConfig:
    """画像処理設定"""
    webp_quality: int = 100
    webp_method: int = 6
    webp_lossless: bool = True
    supported_extensions: List[str] = None

    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = ["webp", "WEBP", "jpg", "png", "JPG", "PNG"]


@dataclass
class LoggingConfig:
    """ログ設定"""
    log_file: str = "LOG.log"
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5


@dataclass
class PatternConfig:
    """正規表現パターン設定"""
    image_pattern: str = r"(?:[＜<〈]画像(?:名|\d*)?(?:（[^）]*）)?[＞>〉]\s*([a-zA-Z0-9\-_]+)|画像名[:：]\s*([a-zA-Z0-9\-_]+))"
    code_pattern: str = r"^(COMFRPTC\d+|GSTFRPTA\d+|THUMBNAIL)"


@dataclass
class AppConfig:
    """アプリケーション設定全体"""
    directories: DirectoryConfig
    image_processing: ImageProcessingConfig
    logging: LoggingConfig
    patterns: PatternConfig
    width_map: Dict[str, List[List[int]]]
    min_width_size_map: Dict[str, Dict[str, Union[int, List[int]]]]

    @classmethod
    def create_default(cls) -> 'AppConfig':
        """デフォルト設定を作成"""
        return cls(
            directories=DirectoryConfig(),
            image_processing=ImageProcessingConfig(),
            logging=LoggingConfig(),
            patterns=PatternConfig(),
            width_map={},
            min_width_size_map={}
        )


class ConfigLoader:
    """JSON設定ファイルを管理するクラス"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        ConfigLoaderを初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self._config: AppConfig = AppConfig.create_default()
        self._raw_config_data: Dict[str, Any] = {}
        self._logger = logging.getLogger(__name__)
        self._load_config()
    
    def _load_config(self) -> None:
        """設定ファイルを読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._raw_config_data = json.load(f)
                    self._config = self._parse_config_from_dict(self._raw_config_data)
                    self._logger.info(f"設定ファイルを読み込みました: {self.config_path}")
            else:
                # デフォルト設定で初期化
                self._logger.info("設定ファイルが存在しないため、デフォルト設定を使用します")
                self._config = AppConfig.create_default()
                self._save_config()
        except Exception as e:
            self._logger.error(f"設定ファイル読み込みエラー: {e}")
            self._config = AppConfig.create_default()
            self._save_config()

    def _parse_config_from_dict(self, config_dict: Dict[str, Any]) -> AppConfig:
        """辞書からAppConfigオブジェクトを作成"""
        try:
            directories = DirectoryConfig(**config_dict.get("directories", {}))
        except TypeError:
            self._logger.warning("ディレクトリ設定の解析に失敗、デフォルト値を使用")
            directories = DirectoryConfig()

        try:
            image_processing = ImageProcessingConfig(**config_dict.get("image_processing", {}))
        except TypeError:
            self._logger.warning("画像処理設定の解析に失敗、デフォルト値を使用")
            image_processing = ImageProcessingConfig()

        try:
            logging_config = LoggingConfig(**config_dict.get("logging", {}))
        except TypeError:
            self._logger.warning("ログ設定の解析に失敗、デフォルト値を使用")
            logging_config = LoggingConfig()

        try:
            patterns = PatternConfig(**config_dict.get("patterns", {}))
        except TypeError:
            self._logger.warning("パターン設定の解析に失敗、デフォルト値を使用")
            patterns = PatternConfig()

        return AppConfig(
            directories=directories,
            image_processing=image_processing,
            logging=logging_config,
            patterns=patterns,
            width_map=config_dict.get("width_map", {}),
            min_width_size_map=config_dict.get("min_width_size_map", {})
        )
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        設定値を取得（後方互換性用）
        
        Args:
            key_path: 設定キーのパス（例: "directories.docx_directory"）
            default: デフォルト値
            
        Returns:
            設定値
        """
        keys = key_path.split('.')
        
        # 型安全なアクセスを試行
        if len(keys) == 2:
            section, key = keys
            if section == "directories":
                return getattr(self._config.directories, key, default)
            elif section == "image_processing":
                return getattr(self._config.image_processing, key, default)
            elif section == "logging":
                return getattr(self._config.logging, key, default)
            elif section == "patterns":
                return getattr(self._config.patterns, key, default)
        
        # フォールバック: 従来の辞書ベースアクセス
        try:
            config_dict = asdict(self._config)
            value = config_dict
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        設定値を設定
        
        Args:
            key_path: 設定キーのパス
            value: 設定値
        """
        keys = key_path.split('.')
        
        # 型安全な設定を試行
        if len(keys) == 2:
            section, key = keys
            try:
                if section == "directories" and hasattr(self._config.directories, key):
                    setattr(self._config.directories, key, value)
                    self._save_config()
                    return
                elif section == "image_processing" and hasattr(self._config.image_processing, key):
                    setattr(self._config.image_processing, key, value)
                    self._save_config()
                    return
                elif section == "logging" and hasattr(self._config.logging, key):
                    setattr(self._config.logging, key, value)
                    self._save_config()
                    return
                elif section == "patterns" and hasattr(self._config.patterns, key):
                    setattr(self._config.patterns, key, value)
                    self._save_config()
                    return
            except Exception as e:
                self._logger.error(f"設定値の設定に失敗: {key_path} = {value}, {e}")
        
        # 特殊なケース（width_map, min_width_size_map）
        if key_path == "width_map":
            self._config.width_map = value
            self._save_config()
        elif key_path == "min_width_size_map":
            self._config.min_width_size_map = value
            self._save_config()
    
    def _save_config(self) -> None:
        """設定をファイルに保存"""
        try:
            # AppConfigを辞書に変換
            config_dict = asdict(self._config)
            
            # ディレクトリが存在しない場合は作成
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            self._logger.info(f"設定ファイルを保存しました: {self.config_path}")
        except Exception as e:
            self._logger.error(f"設定ファイル保存エラー: {e}")

    def save_config(self) -> None:
        """設定をファイルに保存（後方互換性用）"""
        self._save_config()
    
    def reload_config(self) -> None:
        """設定ファイルを再読み込み"""
        self._load_config()
    
    def get_all_config(self) -> Dict[str, Any]:
        """全設定データを取得"""
        return asdict(self._config)
    
    def update_config(self, config_dict: Dict[str, Any]) -> None:
        """設定データを更新"""
        try:
            # 新しい設定をマージ
            updated_config = self._parse_config_from_dict({**asdict(self._config), **config_dict})
            self._config = updated_config
            self._save_config()
        except Exception as e:
            self._logger.error(f"設定データの更新に失敗: {e}")
    
    # 型安全なアクセサメソッド群
    @property
    def config(self) -> AppConfig:
        """設定オブジェクトを取得"""
        return self._config
    
    def get_directories(self) -> DirectoryConfig:
        """ディレクトリ設定を取得"""
        return self._config.directories
    
    def get_image_processing(self) -> ImageProcessingConfig:
        """画像処理設定を取得"""
        return self._config.image_processing
    
    def get_logging_config(self) -> LoggingConfig:
        """ログ設定を取得"""
        return self._config.logging
    
    def get_patterns(self) -> PatternConfig:
        """パターン設定を取得"""
        return self._config.patterns
    
    def get_width_map(self) -> Dict[str, List[List[int]]]:
        """幅マップを取得"""
        return self._config.width_map
    
    def get_min_width_size_map(self) -> Dict[str, Dict[str, Union[int, List[int]]]]:
        """最小幅サイズマップを取得"""
        return self._config.min_width_size_map


# グローバル設定インスタンス
config_loader = ConfigLoader()


# 後方互換性のための関数群
def get_config_value(key_path: str, default: Any = None) -> Any:
    """設定値を取得（後方互換性用）"""
    return config_loader.get(key_path, default)


def set_config_value(key_path: str, value: Any) -> None:
    """設定値を設定（後方互換性用）"""
    config_loader.set(key_path, value)


def save_config() -> None:
    """設定を保存（後方互換性用）"""
    config_loader.save_config()


def reload_config() -> None:
    """設定を再読み込み（後方互換性用）"""
    config_loader.reload_config()
