"""
ファイル管理モジュール（統合クラス）
各種ファイル管理機能を統合して提供
"""

from typing import List, Dict, Optional
import logging

from .directory_manager import DirectoryManager
from .file_scanner import FileScanner
from .result_manager import ResultManager
from ..utils.logger import get_missing_images_count


class FileManager:
    """ファイル管理機能を統合するクラス（Facade Pattern）"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._directory_manager = DirectoryManager()
        self._file_scanner = FileScanner()
        self._result_manager = ResultManager()
    
    def get_docx_files(self) -> List[str]:
        """
        処理対象のDOCXファイル一覧を取得
        
        Returns:
            DOCXファイルのパスのリスト
        """
        return self._file_scanner.get_docx_files()
    
    def validate_docx_files(self, docx_files: List[str]) -> bool:
        """
        DOCXファイルの存在を確認
        
        Args:
            docx_files: DOCXファイルのパスのリスト
            
        Returns:
            有効なファイルが存在する場合True
        """
        return self._file_scanner.validate_docx_files(docx_files)
    
    def create_output_directory(self, docx_file: str) -> str:
        """
        出力ディレクトリを作成
        
        Args:
            docx_file: DOCXファイルのパス
            
        Returns:
            作成された出力ディレクトリのパス
        """
        return self._directory_manager.create_output_directory(docx_file)
    
    def find_html_file(self, docx_file: str) -> Optional[str]:
        """
        DOCXファイルに対応するHTMLファイルを検索
        
        Args:
            docx_file: DOCXファイルのパス
            
        Returns:
            HTMLファイルのパス、見つからない場合はNone
        """
        return self._file_scanner.find_html_file(docx_file)
    
    def save_results(self, all_image_names: List[Dict[str, str]], all_converted_images: List[str]) -> None:
        """
        処理結果をファイルに保存
        
        Args:
            all_image_names: 全ファイルの画像名情報
            all_converted_images: 変換された画像ファイルのパス一覧
        """
        self._result_manager.save_results(all_image_names, all_converted_images)
    
    def display_output_structure(self, docx_files: List[str]) -> None:
        """
        出力ディレクトリ構造を表示
        
        Args:
            docx_files: 処理対象のDOCXファイル一覧
        """
        self._directory_manager.display_output_structure(docx_files)
    
    def ensure_base_directories(self) -> None:
        """
        必要な基本ディレクトリを作成
        """
        self._directory_manager.ensure_base_directories()
    
    def get_file_info(self, docx_file: str) -> Dict[str, str]:
        """
        ファイル情報を取得
        
        Args:
            docx_file: DOCXファイルのパス
            
        Returns:
            ファイル情報の辞書
        """
        return self._file_scanner.get_file_info(docx_file)
    
    def create_summary_report(self, 
                            docx_files: List[str], 
                            all_converted_images: List[str]) -> None:
        """
        処理結果のサマリーレポートを作成・保存
        
        Args:
            docx_files: 処理対象のDOCXファイル一覧
            all_converted_images: 変換された画像ファイルのパス一覧
        """
        missing_images_count = get_missing_images_count()
        summary = self._result_manager.create_summary_report(
            docx_files, all_converted_images, missing_images_count
        )
        self._result_manager.save_summary_report(summary)
