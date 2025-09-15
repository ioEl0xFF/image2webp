"""
GUI設定管理
GUI設定の保存・読み込み・管理を担当
"""

import json
import tkinter as tk
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from ..config.loader import config_loader


class GUISettingsManager:
    """GUI設定を管理するクラス"""
    
    def __init__(self, settings_file: str = "config/gui_settings.json"):
        self._logger = logging.getLogger(__name__)
        self._settings_file = Path(settings_file)
        self._settings: Dict[str, Any] = {}
        self._load_settings()
    
    def _load_settings(self) -> None:
        """設定ファイルを読み込み"""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
                self._logger.info(f"GUI設定を読み込みました: {self._settings_file}")
            else:
                self._settings = self._create_default_settings()
                self._save_settings()
                self._logger.info("デフォルトGUI設定を作成しました")
        except Exception as e:
            self._logger.error(f"GUI設定読み込みエラー: {e}")
            self._settings = self._create_default_settings()
    
    def _create_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定を作成"""
        directories = config_loader.get_directories()
        image_processing = config_loader.get_image_processing()
        
        return {
            "window": {
                "geometry": "800x700",
                "last_position": None
            },
            "directories": {
                "docx_dir": directories.docx_directory,
                "images_dir": directories.images_dir,
                "html_dir": directories.html_dir,
                "output_dir": directories.output_base_dir
            },
            "processing": {
                "webp_quality": image_processing.webp_quality
            },
            "ui": {
                "auto_scroll_log": True,
                "show_progress_details": True,
                "remember_window_state": True
            }
        }
    
    def _save_settings(self) -> None:
        """設定をファイルに保存"""
        try:
            # ディレクトリが存在しない場合は作成
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
            
            self._logger.info(f"GUI設定を保存しました: {self._settings_file}")
        except Exception as e:
            self._logger.error(f"GUI設定保存エラー: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key_path: 設定キーのパス（例: "window.geometry"）
            default: デフォルト値
            
        Returns:
            設定値
        """
        keys = key_path.split('.')
        value = self._settings
        
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
        settings = self._settings
        
        # 最後のキー以外は辞書を作成/取得
        for key in keys[:-1]:
            if key not in settings or not isinstance(settings[key], dict):
                settings[key] = {}
            settings = settings[key]
        
        # 最後のキーに値を設定
        settings[keys[-1]] = value
        self._save_settings()
    
    def get_window_settings(self) -> Dict[str, Any]:
        """ウィンドウ設定を取得"""
        return self.get("window", {})
    
    def save_window_state(self, root: tk.Tk) -> None:
        """ウィンドウ状態を保存"""
        if self.get("ui.remember_window_state", True):
            try:
                geometry = root.geometry()
                self.set("window.geometry", geometry)
                
                # ウィンドウ位置も保存
                x = root.winfo_x()
                y = root.winfo_y()
                self.set("window.last_position", {"x": x, "y": y})
                
            except Exception as e:
                self._logger.error(f"ウィンドウ状態保存エラー: {e}")
    
    def restore_window_state(self, root: tk.Tk) -> None:
        """ウィンドウ状態を復元"""
        if self.get("ui.remember_window_state", True):
            try:
                # ジオメトリを復元
                geometry = self.get("window.geometry", "800x700")
                root.geometry(geometry)
                
                # 位置を復元
                last_pos = self.get("window.last_position")
                if last_pos and isinstance(last_pos, dict):
                    x = last_pos.get("x", 100)
                    y = last_pos.get("y", 100)
                    # 画面外にならないようにチェック
                    screen_width = root.winfo_screenwidth()
                    screen_height = root.winfo_screenheight()
                    
                    if 0 <= x < screen_width - 100 and 0 <= y < screen_height - 100:
                        root.geometry(f"+{x}+{y}")
                        
            except Exception as e:
                self._logger.error(f"ウィンドウ状態復元エラー: {e}")
    
    def get_directory_settings(self) -> Dict[str, str]:
        """ディレクトリ設定を取得"""
        return self.get("directories", {})
    
    def update_directory_settings(self, directories: Dict[str, str]) -> None:
        """ディレクトリ設定を更新"""
        for key, value in directories.items():
            self.set(f"directories.{key}", value)
    
    def get_processing_settings(self) -> Dict[str, Any]:
        """処理設定を取得"""
        return self.get("processing", {})
    
    def update_processing_settings(self, settings: Dict[str, Any]) -> None:
        """処理設定を更新"""
        for key, value in settings.items():
            self.set(f"processing.{key}", value)
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """UI設定を取得"""
        return self.get("ui", {})
    
    def reset_to_defaults(self) -> None:
        """設定をデフォルトにリセット"""
        self._settings = self._create_default_settings()
        self._save_settings()
        self._logger.info("GUI設定をデフォルトにリセットしました")
    
    def export_settings(self, file_path: str) -> bool:
        """設定をファイルにエクスポート"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
            
            self._logger.info(f"GUI設定をエクスポートしました: {file_path}")
            return True
        except Exception as e:
            self._logger.error(f"GUI設定エクスポートエラー: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """設定をファイルからインポート"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # 設定を検証してからマージ
            if self._validate_settings(imported_settings):
                self._settings.update(imported_settings)
                self._save_settings()
                self._logger.info(f"GUI設定をインポートしました: {file_path}")
                return True
            else:
                self._logger.error("インポートされた設定が無効です")
                return False
                
        except Exception as e:
            self._logger.error(f"GUI設定インポートエラー: {e}")
            return False
    
    def _validate_settings(self, settings: Dict[str, Any]) -> bool:
        """設定の妥当性を検証"""
        # 基本的な構造チェック
        required_sections = ["window", "directories", "processing", "ui"]
        return all(section in settings for section in required_sections)
