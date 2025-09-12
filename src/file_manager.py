"""
ファイル管理モジュール
ファイル操作とディレクトリ管理を担当
"""

import os
import json
import glob
from typing import List, Dict
from pathlib import Path

from . import config
from .exceptions import DocxFileError
from .logger_utils import get_logger


class FileManager:
    """ファイル操作を担当するクラス"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def get_docx_files(self) -> List[str]:
        """
        処理対象のDOCXファイル一覧を取得
        
        Returns:
            DOCXファイルのパスのリスト
        """
        docx_files = glob.glob(f"{config.DOCX_DIRECTORY}/*.docx")
        
        # 一時ファイル（~$で始まるファイル）を除外
        docx_files = [f for f in docx_files if not os.path.basename(f).startswith('~$')]
        
        return docx_files
    
    def validate_docx_files(self, docx_files: List[str]) -> bool:
        """
        DOCXファイルの存在を確認
        
        Args:
            docx_files: DOCXファイルのパスのリスト
            
        Returns:
            有効なファイルが存在する場合True
        """
        if not docx_files:
            print(f"[ERROR] {config.DOCX_DIRECTORY} ディレクトリにDOCXファイルが見つかりません")
            self.logger.error(f"DOCXファイルが見つかりません: {config.DOCX_DIRECTORY}")
            return False
        
        print(f"処理対象ファイル数: {len(docx_files)}")
        self.logger.info(f"処理対象ファイル数: {len(docx_files)}")
        for file in docx_files:
            print(f"  - {os.path.basename(file)}")
            self.logger.info(f"処理対象ファイル: {os.path.basename(file)}")
        
        return True
    
    def create_output_directory(self, docx_file: str) -> str:
        """
        出力ディレクトリを作成
        
        Args:
            docx_file: DOCXファイルのパス
            
        Returns:
            作成された出力ディレクトリのパス
        """
        file_name = os.path.basename(docx_file)
        file_name_without_ext = os.path.splitext(file_name)[0]
        output_dir = f"{config.OUTPUT_BASE_DIR}/{file_name_without_ext}"
        
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def find_html_file(self, docx_file: str) -> str:
        """
        DOCXファイルに対応するHTMLファイルを検索
        
        Args:
            docx_file: DOCXファイルのパス
            
        Returns:
            HTMLファイルのパス、見つからない場合は空文字列
        """
        file_name = os.path.basename(docx_file)
        file_name_without_ext = os.path.splitext(file_name)[0]
        html_file_path = os.path.join(config.HTML_DIR, f"{file_name_without_ext}.html")
        
        if os.path.exists(html_file_path):
            print(f"HTMLファイル発見: {html_file_path} を読み込みます")
            self.logger.info(f"HTMLファイル発見: {html_file_path} を読み込み")
            return html_file_path
        else:
            print(f"HTMLファイル未発見: {html_file_path}")
            self.logger.info(f"HTMLファイル未発見: {html_file_path}")
            return ""
    
    def save_results(self, all_image_names: List[Dict[str, str]], all_converted_images: List[str]) -> None:
        """
        処理結果をファイルに保存
        
        Args:
            all_image_names: 全ファイルの画像名情報
            all_converted_images: 変換された画像ファイルのパス一覧
        """
        # 全ファイルの結果をJSON出力（ログディレクトリに保存）
        json_file = Path(config.LOG_DIR) / "all_image_names.json"
        try:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(all_image_names, f, ensure_ascii=False, indent=2)
            print(f"全ファイルの画像名JSON出力完了: {json_file}")
            self.logger.info(f"画像名JSON出力完了: {json_file}")
        except Exception as e:
            self.logger.error(f"JSON出力失敗: {json_file} - {e}")
        
        # 変換成功画像の一覧をファイル出力（ログディレクトリに保存）
        list_file = Path(config.LOG_DIR) / "all_converted_images.txt"
        try:
            with open(list_file, "w", encoding="utf-8") as f:
                f.write("\n".join(all_converted_images))
            
            print(f"全ファイルの変換済み画像一覧を {list_file} に出力しました。")
            print(f"総変換画像数: {len(all_converted_images)}")
            self.logger.info(f"変換済み画像一覧出力完了: {list_file} - 総数: {len(all_converted_images)}")
        except Exception as e:
            self.logger.error(f"変換済み画像一覧出力失敗: {list_file} - {e}")
    
    def display_output_structure(self, docx_files: List[str]) -> None:
        """
        出力ディレクトリ構造を表示
        
        Args:
            docx_files: 処理対象のDOCXファイル一覧
        """
        print("\n=== 出力ディレクトリ構造 ===")
        for docx_file in docx_files:
            file_name = os.path.basename(docx_file)
            file_name_without_ext = os.path.splitext(file_name)[0]
            output_dir = f"{config.OUTPUT_BASE_DIR}/{file_name_without_ext}"
            if os.path.exists(output_dir):
                webp_files = glob.glob(f"{output_dir}/*.webp")
                print(f"{output_dir}/ ({len(webp_files)}個のWebPファイル)")
    
    def ensure_base_directories(self) -> None:
        """
        必要な基本ディレクトリを作成
        """
        # 出力ディレクトリ（ベース）を作成
        os.makedirs(config.OUTPUT_BASE_DIR, exist_ok=True)
        self.logger.info(f"出力ベースディレクトリを確保: {config.OUTPUT_BASE_DIR}")
    
    def get_file_info(self, docx_file: str) -> Dict[str, str]:
        """
        ファイル情報を取得
        
        Args:
            docx_file: DOCXファイルのパス
            
        Returns:
            ファイル情報の辞書
        """
        file_name = os.path.basename(docx_file)
        file_name_without_ext = os.path.splitext(file_name)[0]
        output_dir = f"{config.OUTPUT_BASE_DIR}/{file_name_without_ext}"
        
        return {
            "file_path": docx_file,
            "file_name": file_name,
            "file_name_without_ext": file_name_without_ext,
            "output_dir": output_dir
        }
