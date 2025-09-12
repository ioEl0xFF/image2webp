"""
DOCX解析ユーティリティ
DOCXファイルから画像名を抽出する機能を提供
"""

import re
import os
import glob
from docx import Document  # type: ignore
from typing import List, Dict, Optional

from . import config
from . import image_utils
from .exceptions import DocxFileError
from .logger_utils import get_logger


class DocxAnalyzer:
    """DOCX解析を担当するクラス"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def extract_image_names_from_docx(self, docx_file: str) -> List[Dict[str, str]]:
        """
        DOCXファイルから画像名を抽出

        Args:
            docx_file: DOCXファイルのパス

        Returns:
            画像名情報のリスト。各要素は以下のキーを持つ辞書:
            - file_name: ファイル名
            - output_dir: 出力ディレクトリ
            - row_index: 行インデックス（左セルのテキスト）
            - image_name: 画像名
        """
        file_name = os.path.basename(docx_file)
        file_name_without_ext = os.path.splitext(file_name)[0]
        output_dir = f"{config.OUTPUT_BASE_DIR}/{file_name_without_ext}"

        image_names = []

        try:
            doc = Document(docx_file)
        except Exception as e:
            print(f"[ERROR] ファイル読み込みエラー: {e}")
            self.logger.error(f"DOCXファイル読み込みエラー: {docx_file} - {e}")
            raise DocxFileError(f"DOCXファイル読み込み失敗: {docx_file}") from e

        print("=== テーブル読み込み開始 ===")
        self.logger.info(f"DOCX解析開始: {file_name}")

        # 各テーブルを順番に処理
        for table_index, table in enumerate(doc.tables, start=1):
            image_names.extend(self._process_table(table, table_index, file_name, output_dir))

        # THUMBNAILの画像名を追加
        if image_names:
            thumbnail_images = self._extract_thumbnail_images(image_names, file_name, output_dir)
            image_names.extend(thumbnail_images)

        print("=== 正規表現抽出完了 ===")
        print(f"抽出された画像名数: {len(image_names)}")
        self.logger.info(f"画像名抽出完了: {file_name} - 抽出数: {len(image_names)}")

        return image_names
    
    def _process_table(
        self, 
        table, 
        table_index: int, 
        file_name: str, 
        output_dir: str
    ) -> List[Dict[str, str]]:
        """
        テーブルを処理して画像名を抽出
        
        Args:
            table: DOCXテーブルオブジェクト
            table_index: テーブルのインデックス
            file_name: ファイル名
            output_dir: 出力ディレクトリ
            
        Returns:
            抽出された画像名情報のリスト
        """
        image_names = []
        
        # テーブルの最初の行の左端セル（0番目）から画像コードを取得
        left_text = table.rows[0].cells[0].text.strip().replace("\n", "") if len(table.rows) > 0 else ""
        print(f"[テーブル{table_index}] 左セル（画像コード）: {left_text}")

        # テーブルの各行を処理
        for row_index, row in enumerate(table.rows, start=1):
            # 各行のすべてのセルを処理（2列でも3列でも対応）
            for cell_index, cell in enumerate(row.cells):
                cell_text = cell.text

                # セル内のテキストを改行で分割して1行ずつ処理
                for line in cell_text.splitlines():
                    line = line.strip()
                    if not line:  # 空行はスキップ
                        continue

                    print(f"  行{row_index} 列{cell_index + 1}: {line}")

                    # 正規表現パターンで画像名を検索
                    matches = re.findall(config.IMAGE_PATTERN, line)
                    if matches:
                        print(f"    マッチ: {matches}")

                    # マッチした画像名を1つずつ処理
                    for match in matches:
                        # matchはタプルなので、空でない最初の要素を取得
                        image_name = next((m for m in match if m), "").strip()
                        if image_name:  # 空でない場合のみ追加
                            image_names.append({
                                "file_name": file_name,           # DOCXファイル名
                                "output_dir": output_dir,         # 出力先ディレクトリ
                                "row_index": left_text,           # 画像コード（左セル）
                                "image_name": image_name          # 抽出された画像名
                            })
        
        return image_names
    
    def _extract_thumbnail_images(
        self, 
        image_names: List[Dict[str, str]], 
        file_name: str, 
        output_dir: str
    ) -> List[Dict[str, str]]:
        """
        THUMBNAILの画像名を抽出
        
        Args:
            image_names: 既存の画像名情報のリスト
            file_name: ファイル名
            output_dir: 出力ディレクトリ
            
        Returns:
            THUMBNAIL画像名情報のリスト
        """
        print("=== THUMBNAILの画像名追加処理開始 ===")
        
        additional_matches = []
        for image_info in image_names:
            image_name = image_info["image_name"]
            new_name = ""
            
            # "-kv" または "_kv" を含むか判定
            if re.search(r'.*-kv', image_name):
                # "-kv" を "-thumbnail" に置換
                new_name = re.sub(r'-kv', '-thumbnail', image_name)
            elif re.search(r'.*_kv', image_name):
                # "_kv" を "_thumbnail" に置換
                new_name = re.sub(r'_kv', '_thumbnail', image_name)

            # imageディレクトリに画像が存在するか確認(拡張子は無視)
            if new_name and image_utils.find_input_image(new_name):
                additional_matches.append(new_name)

        thumbnail_images = []
        if additional_matches:
            print(f"追加された画像名: {additional_matches}")
            self.logger.info(f"追加された画像名: {additional_matches}")

            # thumbnail画像情報を作成
            for thumbnail_name in additional_matches:
                thumbnail_images.append({
                    "file_name": file_name,
                    "output_dir": output_dir,
                    "row_index": "THUMBNAIL",
                    "image_name": thumbnail_name.strip()
                })
        
        return thumbnail_images


# 後方互換性のための関数（既存コードとの互換性を保持）
def extract_image_names_from_docx(docx_file: str) -> List[Dict[str, str]]:
    """
    DOCXファイルから画像名を抽出（後方互換性のためのラッパー関数）
    
    Args:
        docx_file: DOCXファイルのパス
        
    Returns:
        画像名情報のリスト
    """
    analyzer = DocxAnalyzer()
    return analyzer.extract_image_names_from_docx(docx_file)


def get_docx_files() -> List[str]:
    """
    処理対象のDOCXファイル一覧を取得

    Returns:
        DOCXファイルのパスのリスト
    """
    import glob

    docx_files = glob.glob(f"{config.DOCX_DIRECTORY}/*.docx")

    # 一時ファイル（~$で始まるファイル）を除外
    docx_files = [f for f in docx_files if not os.path.basename(f).startswith('~$')]

    return docx_files


def validate_docx_files(docx_files: List[str]) -> bool:
    """
    DOCXファイルの存在を確認

    Args:
        docx_files: DOCXファイルのパスのリスト

    Returns:
        有効なファイルが存在する場合True
    """
    logger = get_logger(__name__)
    if not docx_files:
        print(f"[ERROR] {config.DOCX_DIRECTORY} ディレクトリにDOCXファイルが見つかりません")
        logger.error(f"DOCXファイルが見つかりません: {config.DOCX_DIRECTORY}")
        return False

    print(f"処理対象ファイル数: {len(docx_files)}")
    logger.info(f"処理対象ファイル数: {len(docx_files)}")
    for file in docx_files:
        print(f"  - {os.path.basename(file)}")
        logger.info(f"処理対象ファイル: {os.path.basename(file)}")

    return True
