"""
メイン処理（リファクタリング版）
DOCXファイルから画像名を抽出し、WebP形式に変換する
"""

import os
from typing import List, Dict, Tuple

from . import config
from .exceptions import Img2WebpError
from .logger_utils import setup_logging, get_missing_images_count
from .file_manager import FileManager
from .docx_parser import DocxAnalyzer
from .image_processor import ImageProcessor
from .html_processor import HtmlProcessor


class Img2WebpProcessor:
    """画像変換処理の統合クラス"""

    def __init__(self):
        self.logger = setup_logging()
        self.file_manager = FileManager()
        self.docx_analyzer = DocxAnalyzer()
        self.image_processor = ImageProcessor()
        self.html_processor = HtmlProcessor()

    def run(self) -> None:
        """メイン処理を実行"""
        try:
            self.logger.info("=== 画像変換処理開始 ===")

            # DOCXファイル一覧取得と検証
            docx_files = self._get_and_validate_docx_files()
            if not docx_files:
                return

            # 必要なディレクトリを準備
            self.file_manager.ensure_base_directories()

            # 全ファイル処理
            all_converted_images, all_image_names = self._process_all_files(docx_files)

            # 処理結果の表示と保存
            self._display_and_save_results(all_converted_images, all_image_names, docx_files)

            self.logger.info("=== 画像変換処理終了 ===")

        except Img2WebpError as e:
            self.logger.error(f"アプリケーションエラー: {e}")
            print(f"[ERROR] 処理中にエラーが発生しました: {e}")
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            print(f"[ERROR] 予期しないエラーが発生しました: {e}")

    def _get_and_validate_docx_files(self) -> List[str]:
        """DOCXファイル一覧を取得し検証"""
        docx_files = self.file_manager.get_docx_files()

        if not self.file_manager.validate_docx_files(docx_files):
            self.logger.error("DOCXファイルの検証に失敗しました")
            return []

        return docx_files

    def _process_all_files(self, docx_files: List[str]) -> Tuple[List[str], List[Dict[str, str]]]:
        """全ファイルを処理"""
        all_converted_images = []
        all_image_names = []

        for file_index, docx_file in enumerate(docx_files, start=1):
            try:
                converted_images, image_names = self._process_single_file(
                    docx_file, file_index, len(docx_files)
                )

                all_converted_images.extend(converted_images)
                all_image_names.extend(image_names)

            except Exception as e:
                self.logger.error(f"ファイル処理エラー: {docx_file} - {e}")
                print(f"[ERROR] ファイル処理に失敗しました: {os.path.basename(docx_file)}")
                continue

        return all_converted_images, all_image_names

    def _process_single_file(
        self,
        docx_file: str,
        file_index: int,
        total_files: int
    ) -> Tuple[List[str], List[Dict[str, str]]]:
        """単一ファイルを処理"""
        file_info = self.file_manager.get_file_info(docx_file)

        print(f"\n=== ファイル {file_index}/{total_files}: {file_info['file_name']} ===")
        print(f"出力ディレクトリ: {file_info['output_dir']}")
        self.logger.info(f"ファイル処理開始: {file_info['file_name']} (出力ディレクトリ: {file_info['output_dir']})")

        # 出力ディレクトリを作成
        self.file_manager.create_output_directory(docx_file)

        # DOCXから画像名抽出
        image_names = self.docx_analyzer.extract_image_names_from_docx(docx_file)

        # HTML画像名置換処理
        self._process_html_if_exists(docx_file, image_names)

        # 画像変換処理
        converted_images = self.image_processor.process_images(image_names, file_info)

        return converted_images, image_names

    def _process_html_if_exists(self, docx_file: str, image_names: List[Dict[str, str]]) -> None:
        """HTMLファイルが存在する場合は画像名置換処理を実行"""
        html_file_path = self.file_manager.find_html_file(docx_file)

        if html_file_path and image_names:
            print("=== HTML画像名置換処理開始 ===")
            success = self.html_processor.process_html_file(html_file_path, image_names)
            if not success:
                self.logger.warning(f"HTML処理に失敗: {html_file_path}")

    def _display_and_save_results(
        self,
        all_converted_images: List[str],
        all_image_names: List[Dict[str, str]],
        docx_files: List[str]
    ) -> None:
        """処理結果の表示と保存"""
        print("\n=== 全ファイル処理完了 ===")
        self.logger.info(f"全ファイル処理完了 - 総変換画像数: {len(all_converted_images)}")

        # 存在しない画像の件数を表示
        self._display_missing_images_count()

        # 結果保存
        self.file_manager.save_results(all_image_names, all_converted_images)

        # 出力構造表示
        self.file_manager.display_output_structure(docx_files)

    def _display_missing_images_count(self) -> None:
        """存在しない画像の件数を表示"""
        missing_count = get_missing_images_count()
        if missing_count > 0:
            print(f"存在しない画像ファイル数: {missing_count}")
            print(f"詳細は {config.LOG_DIR}/missing_images.txt を確認してください")
            self.logger.info(f"存在しない画像ファイル数: {missing_count}")


def main():
    """メイン関数"""
    processor = Img2WebpProcessor()
    processor.run()


if __name__ == "__main__":
    main()
