"""
ディレクトリ管理モジュール
ディレクトリの作成・検証・構造表示を担当
"""

import os
import glob
from pathlib import Path
from typing import List, Optional
import logging

from ..config.loader import config_loader


class DirectoryManager:
    """ディレクトリ操作を担当するクラス"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._config = config_loader.get_directories()
    
    def ensure_base_directories(self) -> None:
        """
        必要な基本ディレクトリを作成
        """
        directories = [
            self._config.output_base_dir,
            self._config.log_dir,
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                self._logger.info(f"ディレクトリを確保: {directory}")
            except OSError as e:
                self._logger.error(f"ディレクトリ作成失敗: {directory} - {e}")
                raise
    
    def create_output_directory(self, docx_file: str) -> str:
        """
        DOCXファイル用の出力ディレクトリを作成
        
        Args:
            docx_file: DOCXファイルのパス
            
        Returns:
            作成された出力ディレクトリのパス
            
        Raises:
            OSError: ディレクトリ作成に失敗した場合
        """
        file_name = Path(docx_file).stem
        output_dir = Path(self._config.output_base_dir) / file_name
        
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            self._logger.info(f"出力ディレクトリを作成: {output_dir}")
            return str(output_dir)
        except OSError as e:
            self._logger.error(f"出力ディレクトリ作成失敗: {output_dir} - {e}")
            raise
    
    def display_output_structure(self, docx_files: List[str]) -> None:
        """
        出力ディレクトリ構造を表示
        
        Args:
            docx_files: 処理対象のDOCXファイル一覧
        """
        print("\n=== 出力ディレクトリ構造 ===")
        
        for docx_file in docx_files:
            file_name = Path(docx_file).stem
            output_dir = Path(self._config.output_base_dir) / file_name
            
            if output_dir.exists():
                webp_files = list(output_dir.glob("*.webp"))
                print(f"{output_dir}/ ({len(webp_files)}個のWebPファイル)")
                self._logger.info(f"出力ディレクトリ: {output_dir} - {len(webp_files)}個のWebPファイル")
            else:
                print(f"{output_dir}/ (ディレクトリが存在しません)")
                self._logger.warning(f"出力ディレクトリが存在しません: {output_dir}")
    
    def get_output_directory_path(self, docx_file: str) -> str:
        """
        DOCXファイルに対応する出力ディレクトリパスを取得
        
        Args:
            docx_file: DOCXファイルのパス
            
        Returns:
            出力ディレクトリのパス
        """
        file_name = Path(docx_file).stem
        return str(Path(self._config.output_base_dir) / file_name)
    
    def validate_input_directories(self) -> bool:
        """
        入力ディレクトリの存在を確認
        
        Returns:
            すべての必要なディレクトリが存在する場合True
        """
        required_dirs = [
            self._config.docx_directory,
            self._config.images_dir,
        ]
        
        all_exist = True
        for directory in required_dirs:
            if not Path(directory).exists():
                self._logger.warning(f"必要なディレクトリが存在しません: {directory}")
                all_exist = False
        
        return all_exist
