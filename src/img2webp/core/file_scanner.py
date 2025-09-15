"""
ファイル検索モジュール
ファイルの検索・検証・情報取得を担当
"""

import os
import glob
from pathlib import Path
from typing import List, Dict, Optional
import logging

from ..config.loader import config_loader
from ..utils.exceptions import DocxFileError


class FileScanner:
    """ファイル検索・検証を担当するクラス"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._config = config_loader.get_directories()

    def get_docx_files(self) -> List[str]:
        """
        処理対象のDOCXファイル一覧を取得

        Returns:
            DOCXファイルのパスのリスト

        Raises:
            DocxFileError: DOCXディレクトリが存在しない場合
        """
        docx_dir = Path(self._config.docx_directory)

        if not docx_dir.exists():
            raise DocxFileError(f"DOCXディレクトリが存在しません: {docx_dir}")

        # DOCXファイルを検索
        docx_files = list(docx_dir.glob("*.docx"))

        # 一時ファイル（~$で始まるファイル）を除外
        docx_files = [str(f) for f in docx_files if not f.name.startswith('~$')]

        self._logger.info(f"DOCXファイル検索完了: {len(docx_files)}個のファイルを発見")
        return docx_files

    def validate_docx_files(self, docx_files: List[str]) -> bool:
        """
        DOCXファイルの存在と有効性を確認

        Args:
            docx_files: DOCXファイルのパスのリスト

        Returns:
            有効なファイルが存在する場合True
        """
        if not docx_files:
            self._logger.error(f"DOCXファイルが見つかりません: {self._config.docx_directory}")
            return False

        # ファイルの存在確認
        valid_files = []
        for file_path in docx_files:
            if Path(file_path).exists() and Path(file_path).is_file():
                valid_files.append(file_path)
            else:
                self._logger.warning(f"無効なファイル: {file_path}")

        if not valid_files:
            self._logger.error("有効なDOCXファイルが見つかりません")
            return False

        self._logger.info(f"処理対象ファイル数: {len(valid_files)}")

        for file_path in valid_files:
            file_name = Path(file_path).name
            self._logger.debug(f"処理対象ファイル: {file_name}")

        return True

    def find_html_file(self, docx_file: str) -> Optional[str]:
        """
        DOCXファイルに対応するHTMLファイルを検索

        Args:
            docx_file: DOCXファイルのパス

        Returns:
            HTMLファイルのパス、見つからない場合はNone
        """
        file_stem = Path(docx_file).stem
        html_file_path = Path(self._config.html_dir) / f"{file_stem}.html"

        if html_file_path.exists():
            self._logger.info(f"HTMLファイル発見: {html_file_path} を読み込み")
            return str(html_file_path)
        else:
            self._logger.info(f"HTMLファイル未発見: {html_file_path}")
            return None

    def get_file_info(self, docx_file: str) -> Dict[str, str]:
        """
        ファイル情報を取得

        Args:
            docx_file: DOCXファイルのパス

        Returns:
            ファイル情報の辞書
        """
        docx_path = Path(docx_file)
        file_name = docx_path.name
        file_stem = docx_path.stem
        output_dir = Path(self._config.output_base_dir) / file_stem

        return {
            "file_path": str(docx_path),
            "file_name": file_name,
            "file_name_without_ext": file_stem,
            "output_dir": str(output_dir)
        }

    def find_image_file(self, image_name: str) -> Optional[str]:
        """
        画像ファイルを検索

        Args:
            image_name: 画像名（拡張子なし）

        Returns:
            見つかった画像ファイルのパス、見つからない場合はNone
        """
        images_dir = Path(self._config.images_dir)

        if not images_dir.exists():
            self._logger.warning(f"画像ディレクトリが存在しません: {images_dir}")
            return None

        # サポートされている拡張子で検索
        supported_extensions = config_loader.get_image_processing().supported_extensions

        for ext in supported_extensions:
            image_file = images_dir / f"{image_name}.{ext}"
            if image_file.exists():
                self._logger.debug(f"画像ファイル発見: {image_file}")
                return str(image_file)

        self._logger.debug(f"画像ファイルが見つかりません: {image_name}")
        return None
