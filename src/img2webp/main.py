"""
メイン処理（リファクタリング版）
DOCXファイルから画像名を抽出し、WebP形式に変換する
"""

import os
import signal
import sys
from typing import List, Dict, Tuple

from .config.loader import config_loader
from .utils.exceptions import Img2WebpError
from .utils.logger import setup_logging, get_missing_images_count
from .utils.error_handler import ErrorHandler, safe_file_operation
from .core.file_manager import FileManager
from .core.docx_parser import DocxAnalyzer
from .core.image_processor import ImageProcessor
from .core.html_processor import HtmlProcessor


class Img2WebpProcessor:
    """画像変換処理の統合クラス"""

    def __init__(self):
        self._logger = setup_logging()
        self._error_handler = ErrorHandler(__name__)
        self._file_manager = FileManager()
        self._docx_analyzer = DocxAnalyzer()
        self._image_processor = ImageProcessor()
        self._html_processor = HtmlProcessor()
        self._config = config_loader.get_directories()
        self._is_cancelled = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """シグナルハンドラーを設定（Ctrl+C対応）"""
        try:
            # メインスレッドでのみシグナルハンドラーを設定
            import threading
            if threading.current_thread() is threading.main_thread():
                def signal_handler(signum, frame):
                    self._logger.info("中断要求を受信しました - 現在の処理を安全に終了しています")
                    self._is_cancelled = True
                    if hasattr(self, '_image_processor'):
                        self._image_processor.cancel_processing()

                # SIGINT (Ctrl+C) のハンドラーを設定
                signal.signal(signal.SIGINT, signal_handler)

                # Windows以外ではSIGTERMも処理
                if hasattr(signal, 'SIGTERM'):
                    signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            # シグナルハンドラーの設定に失敗した場合は無視
            # GUIモードなどでは設定できない場合がある
            pass

    def run(self) -> None:
        """メイン処理を実行"""
        try:
            self._logger.info("=== 画像変換処理開始 ===")

            # DOCXファイル一覧取得と検証
            docx_files = self._get_and_validate_docx_files()
            if not docx_files:
                return

            # 中断チェック
            if self._is_cancelled:
                self._logger.info("処理が中断されました")
                return

            # 必要なディレクトリを準備
            self._file_manager.ensure_base_directories()

            # 中断チェック
            if self._is_cancelled:
                self._logger.info("処理が中断されました")
                return

            # 全ファイル処理
            all_converted_images, all_image_names = self._process_all_files(docx_files)

            # 中断チェック
            if self._is_cancelled:
                self._logger.info(f"処理が中断されました - 部分的に処理されたファイル: {len(all_converted_images)} 個")
                return

            # 処理結果の表示と保存
            self._display_and_save_results(all_converted_images, all_image_names, docx_files)

            if not self._is_cancelled:
                self._logger.info("=== 画像変換処理終了 ===")
            else:
                self._logger.info("=== 画像変換処理中断 ===")

        except Img2WebpError as e:
            self._error_handler.handle_error(e, "メイン処理", reraise=False)
        except KeyboardInterrupt:
            # Ctrl+C による中断
            self._logger.info("処理がユーザーによって中断されました")
        except Exception as e:
            self._error_handler.handle_error(e, "メイン処理", reraise=False)
        finally:
            # リソースのクリーンアップ
            self._cleanup_resources()

    def _cleanup_resources(self):
        """リソースのクリーンアップ"""
        try:
            # 画像プロセッサーのリセット
            if hasattr(self, '_image_processor'):
                self._image_processor._is_cancelled = False

            # ログハンドラーのクリーンアップ
            if hasattr(self, '_logger'):
                handlers = self._logger.handlers[:]
                for handler in handlers:
                    handler.close()
                    self._logger.removeHandler(handler)

        except Exception as e:
            # クリーンアップ中のエラーは無視
            pass

    def _get_and_validate_docx_files(self) -> List[str]:
        """DOCXファイル一覧を取得し検証"""
        docx_files = self._file_manager.get_docx_files()

        if not self._file_manager.validate_docx_files(docx_files):
            self._logger.error("DOCXファイルの検証に失敗しました")
            return []

        return docx_files

    def _process_all_files(self, docx_files: List[str]) -> Tuple[List[str], List[Dict[str, str]]]:
        """全ファイルを処理"""
        all_converted_images = []
        all_image_names = []

        for file_index, docx_file in enumerate(docx_files, start=1):
            # 中断チェック
            if self._is_cancelled:
                self._logger.info(f"ファイル処理が中断されました ({file_index-1}/{len(docx_files)})")
                break

            try:
                converted_images, image_names = self._process_single_file(
                    docx_file, file_index, len(docx_files)
                )

                all_converted_images.extend(converted_images)
                all_image_names.extend(image_names)

            except Exception as e:
                self._logger.error(f"ファイル処理エラー: {docx_file} - {e}")
                continue

        return all_converted_images, all_image_names

    def _process_single_file(
        self,
        docx_file: str,
        file_index: int,
        total_files: int
    ) -> Tuple[List[str], List[Dict[str, str]]]:
        """単一ファイルを処理"""
        file_info = self._file_manager.get_file_info(docx_file)

        self._logger.info(f"ファイル処理開始 ({file_index}/{total_files}): {file_info['file_name']} (出力ディレクトリ: {file_info['output_dir']})")

        # 出力ディレクトリを作成
        self._file_manager.create_output_directory(docx_file)

        # DOCXから画像名抽出
        image_names = self._docx_analyzer.extract_image_names_from_docx(docx_file)

        # HTML画像名置換処理
        self._process_html_if_exists(docx_file, image_names)

        # 画像変換処理
        converted_images = self._image_processor.process_images(image_names, file_info)

        return converted_images, image_names

    def _process_html_if_exists(self, docx_file: str, image_names: List[Dict[str, str]]) -> None:
        """HTMLファイルが存在する場合は画像名置換処理を実行"""
        html_file_path = self._file_manager.find_html_file(docx_file)

        if html_file_path and image_names:
            self._logger.info("HTML画像名置換処理開始")
            success = self._html_processor.process_html_file(html_file_path, image_names)
            if not success:
                self._logger.warning(f"HTML処理に失敗: {html_file_path}")

    def _display_and_save_results(
        self,
        all_converted_images: List[str],
        all_image_names: List[Dict[str, str]],
        docx_files: List[str]
    ) -> None:
        """処理結果の表示と保存"""
        self._logger.info(f"全ファイル処理完了 - 総変換画像数: {len(all_converted_images)}")

        # 存在しない画像の件数を表示
        self._display_missing_images_count()

        # 結果保存
        self._file_manager.save_results(all_image_names, all_converted_images)

        # サマリーレポート作成
        self._file_manager.create_summary_report(docx_files, all_converted_images)

        # 出力構造表示
        self._file_manager.display_output_structure(docx_files)

    def _display_missing_images_count(self) -> None:
        """存在しない画像の件数を表示"""
        missing_count = get_missing_images_count()
        if missing_count > 0:
            self._logger.info(f"存在しない画像ファイル数: {missing_count} - 詳細は {self._config.log_dir}/missing_images.txt を確認してください")


def main():
    """メイン関数"""
    processor = Img2WebpProcessor()
    processor.run()


if __name__ == "__main__":
    main()
