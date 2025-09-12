"""
JSON設定ファイルローダー
config.jsonから設定を読み込み、アプリケーション全体で使用する設定値を管理
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Union


class ConfigLoader:
    """JSON設定ファイルを管理するクラス"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        ConfigLoaderを初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self._config_data = {}
        self._load_config()
    
    def _load_config(self):
        """設定ファイルを読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
            else:
                # デフォルト設定で初期化
                self._create_default_config()
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """デフォルト設定を作成"""
        self._config_data = {
            "directories": {
                "docx_directory": "docxs",
                "output_base_dir": "output",
                "images_dir": "images",
                "html_dir": "html",
                "log_dir": ".logs"
            },
            "image_processing": {
                "webp_quality": 100,
                "webp_method": 6,
                "webp_lossless": True,
                "supported_extensions": ["webp", "WEBP", "jpg", "png", "JPG", "PNG"]
            },
            "logging": {
                "log_file": "LOG.log",
                "log_level": "INFO",
                "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "log_date_format": "%Y-%m-%d %H:%M:%S"
            },
            "patterns": {
                "image_pattern": r"(?:[＜<〈]画像(?:名|\d*)?(?:（[^）]*）)?[＞>〉]\s*([a-zA-Z0-9\-_]+)|画像名[:：]\s*([a-zA-Z0-9\-_]+))",
                "code_pattern": r"^(COMFRPTC\d+|GSTFRPTA\d+|THUMBNAIL)"
            },
            "width_map": {},
            "min_width_size_map": {}
        }
        self.save_config()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key_path: 設定キーのパス（例: "directories.docx_directory"）
            default: デフォルト値
            
        Returns:
            設定値
        """
        keys = key_path.split('.')
        value = self._config_data
        
        try:
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
        config = self._config_data
        
        # 最後のキー以外は辞書を作成/取得
        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
        
        # 最後のキーに値を設定
        config[keys[-1]] = value
    
    def save_config(self) -> None:
        """設定をファイルに保存"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
    
    def reload_config(self) -> None:
        """設定ファイルを再読み込み"""
        self._load_config()
    
    def get_all_config(self) -> Dict[str, Any]:
        """全設定データを取得"""
        return self._config_data.copy()
    
    def update_config(self, config_dict: Dict[str, Any]) -> None:
        """設定データを更新"""
        self._config_data.update(config_dict)
    
    # 便利メソッド群
    def get_directories(self) -> Dict[str, str]:
        """ディレクトリ設定を取得"""
        return self.get("directories", {})
    
    def get_image_processing(self) -> Dict[str, Any]:
        """画像処理設定を取得"""
        return self.get("image_processing", {})
    
    def get_logging(self) -> Dict[str, Any]:
        """ログ設定を取得"""
        return self.get("logging", {})
    
    def get_patterns(self) -> Dict[str, str]:
        """パターン設定を取得"""
        return self.get("patterns", {})
    
    def get_width_map(self) -> Dict[str, List[List[int]]]:
        """幅マップを取得"""
        return self.get("width_map", {})
    
    def get_min_width_size_map(self) -> Dict[str, Dict[str, Union[int, List[int]]]]:
        """最小幅サイズマップを取得"""
        return self.get("min_width_size_map", {})


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
