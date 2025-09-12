"""
GUI用カスタマイズプロセッサー
既存のImg2WebpProcessorをGUIアプリケーション用に拡張
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
import queue
import threading

from . import config
from .main import Img2WebpProcessor
from .exceptions import Img2WebpError
from .logger_utils import setup_logging


class GuiLogHandler(logging.Handler):
    """GUI用ログハンドラー"""
    
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        """ログレコードをキューに送信"""
        try:
            message = self.format(record)
            level_map = {
                logging.DEBUG: "info",
                logging.INFO: "info", 
                logging.WARNING: "warning",
                logging.ERROR: "error",
                logging.CRITICAL: "error"
            }
            level = level_map.get(record.levelno, "info")
            self.log_queue.put((message, level))
        except Exception:
            # ログ処理でエラーが発生した場合は無視
            pass


class GuiImg2WebpProcessor(Img2WebpProcessor):
    """GUI用にカスタマイズされたプロセッサー"""
    
    def __init__(self, log_queue: queue.Queue, gui_settings: Optional[Dict] = None):
        """
        初期化
        
        Args:
            log_queue: GUIにログを送信するためのキュー
            gui_settings: GUI設定（ディレクトリパス、品質など）
        """
        # 設定を一時的に変更
        self._original_config = {}
        if gui_settings:
            self._apply_gui_settings(gui_settings)
        
        # 親クラスの初期化
        super().__init__()
        
        # GUI用ログハンドラーを追加
        self.log_queue = log_queue
        self._setup_gui_logging()
        
        # 処理状態
        self.is_cancelled = False
        self.current_file_index = 0
        self.total_files = 0
    
    def _apply_gui_settings(self, settings: Dict):
        """GUI設定を適用"""
        # 元の設定を保存
        self._original_config = {
            'DOCX_DIRECTORY': config.DOCX_DIRECTORY,
            'IMAGES_DIR': config.IMAGES_DIR,
            'HTML_DIR': config.HTML_DIR,
            'OUTPUT_BASE_DIR': config.OUTPUT_BASE_DIR,
            'WEBP_QUALITY': config.WEBP_QUALITY
        }
        
        # GUI設定を適用
        if 'docx_dir' in settings:
            config.DOCX_DIRECTORY = settings['docx_dir']
        if 'images_dir' in settings:
            config.IMAGES_DIR = settings['images_dir']
        if 'html_dir' in settings:
            config.HTML_DIR = settings['html_dir']
        if 'output_dir' in settings:
            config.OUTPUT_BASE_DIR = settings['output_dir']
        if 'webp_quality' in settings:
            config.WEBP_QUALITY = settings['webp_quality']
    
    def _setup_gui_logging(self):
        """GUI用ログ設定"""
        gui_handler = GuiLogHandler(self.log_queue)
        gui_handler.setLevel(logging.INFO)
        
        # フォーマッター設定
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                    datefmt='%H:%M:%S')
        gui_handler.setFormatter(formatter)
        
        # ルートロガーに追加
        root_logger = logging.getLogger()
        root_logger.addHandler(gui_handler)
        
        # 既存のハンドラーのレベルを調整
        self.logger.addHandler(gui_handler)
    
    def cancel_processing(self):
        """処理をキャンセル"""
        self.is_cancelled = True
        self.log_queue.put(("処理のキャンセルが要求されました", "warning"))
    
    def run(self) -> None:
        """メイン処理を実行（GUI対応版）"""
        try:
            self.log_queue.put(("=== 画像変換処理開始 ===", "info"))
            
            # DOCXファイル一覧取得と検証
            docx_files = self._get_and_validate_docx_files()
            if not docx_files:
                self.log_queue.put(("処理対象のDOCXファイルが見つかりません", "warning"))
                return
            
            self.total_files = len(docx_files)
            self.log_queue.put((f"処理対象ファイル数: {self.total_files}", "info"))
            
            # キャンセルチェック
            if self.is_cancelled:
                return
            
            # 必要なディレクトリを準備
            self.file_manager.ensure_base_directories()
            
            # 全ファイル処理
            all_converted_images, all_image_names = self._process_all_files_gui(docx_files)
            
            # キャンセルチェック
            if self.is_cancelled:
                self.log_queue.put(("処理がキャンセルされました", "warning"))
                return
            
            # 処理結果の表示と保存
            self._display_and_save_results_gui(all_converted_images, all_image_names, docx_files)
            
            self.log_queue.put(("=== 画像変換処理終了 ===", "success"))
            
        except Img2WebpError as e:
            self.log_queue.put((f"アプリケーションエラー: {e}", "error"))
            raise
        except Exception as e:
            self.log_queue.put((f"予期しないエラー: {e}", "error"))
            raise
        finally:
            # 設定を元に戻す
            self._restore_original_config()
    
    def _process_all_files_gui(self, docx_files: List[str]) -> Tuple[List[str], List[Dict[str, str]]]:
        """全ファイルを処理（GUI対応版）"""
        all_converted_images = []
        all_image_names = []
        
        for file_index, docx_file in enumerate(docx_files, start=1):
            # キャンセルチェック
            if self.is_cancelled:
                break
            
            self.current_file_index = file_index
            
            try:
                # 進捗をGUIに通知
                file_name = os.path.basename(docx_file)
                progress_msg = f"処理中 ({file_index}/{self.total_files}): {file_name}"
                self.log_queue.put((progress_msg, "info"))
                
                converted_images, image_names = self._process_single_file(
                    docx_file, file_index, len(docx_files)
                )
                
                all_converted_images.extend(converted_images)
                all_image_names.extend(image_names)
                
                # 完了をGUIに通知
                self.log_queue.put((f"完了: {file_name} (変換画像数: {len(converted_images)})", "success"))
                
            except Exception as e:
                error_msg = f"ファイル処理エラー: {os.path.basename(docx_file)} - {e}"
                self.log_queue.put((error_msg, "error"))
                self.logger.error(error_msg)
                continue
        
        return all_converted_images, all_image_names
    
    def _display_and_save_results_gui(
        self,
        all_converted_images: List[str],
        all_image_names: List[Dict[str, str]],
        docx_files: List[str]
    ) -> None:
        """処理結果の表示と保存（GUI対応版）"""
        total_converted = len(all_converted_images)
        self.log_queue.put((f"全ファイル処理完了 - 総変換画像数: {total_converted}", "success"))
        
        # 存在しない画像の件数を表示
        self._display_missing_images_count_gui()
        
        # 結果保存
        try:
            self.file_manager.save_results(all_image_names, all_converted_images)
            self.log_queue.put(("処理結果を保存しました", "info"))
        except Exception as e:
            self.log_queue.put((f"結果保存エラー: {e}", "error"))
        
        # 出力構造表示
        try:
            self.file_manager.display_output_structure(docx_files)
        except Exception as e:
            self.log_queue.put((f"出力構造表示エラー: {e}", "warning"))
    
    def _display_missing_images_count_gui(self) -> None:
        """存在しない画像の件数を表示（GUI版）"""
        try:
            from .logger_utils import get_missing_images_count
            missing_count = get_missing_images_count()
            if missing_count > 0:
                missing_msg = f"存在しない画像ファイル数: {missing_count} (詳細: {config.LOG_DIR}/missing_images.txt)"
                self.log_queue.put((missing_msg, "warning"))
        except Exception as e:
            self.log_queue.put((f"存在しない画像の確認でエラー: {e}", "warning"))
    
    def _restore_original_config(self):
        """元の設定を復元"""
        if self._original_config:
            for key, value in self._original_config.items():
                setattr(config, key, value)
    
    def get_progress_info(self) -> Dict:
        """現在の進捗情報を取得"""
        return {
            'current_file': self.current_file_index,
            'total_files': self.total_files,
            'is_cancelled': self.is_cancelled
        }


class ProcessorThread(threading.Thread):
    """プロセッサー実行用スレッド"""
    
    def __init__(self, log_queue: queue.Queue, gui_settings: Dict):
        super().__init__(daemon=True)
        self.log_queue = log_queue
        self.gui_settings = gui_settings
        self.processor = None
        self.exception = None
        
    def run(self):
        """スレッド実行"""
        try:
            self.processor = GuiImg2WebpProcessor(self.log_queue, self.gui_settings)
            self.processor.run()
        except Exception as e:
            self.exception = e
            self.log_queue.put((f"処理エラー: {str(e)}", "error"))
    
    def cancel(self):
        """処理をキャンセル"""
        if self.processor:
            self.processor.cancel_processing()
    
    def get_progress_info(self) -> Dict:
        """進捗情報を取得"""
        if self.processor:
            return self.processor.get_progress_info()
        return {'current_file': 0, 'total_files': 0, 'is_cancelled': False}
