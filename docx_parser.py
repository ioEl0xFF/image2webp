"""
DOCX解析ユーティリティ
DOCXファイルから画像名を抽出する機能を提供
"""

import re
import os
import logging
from docx import Document
from typing import List, Dict
import config

import image_utils


def extract_image_names_from_docx(docx_file: str) -> List[Dict[str, str]]:
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

    logger = logging.getLogger(__name__)
    try:
        doc = Document(docx_file)
    except Exception as e:
        print(f"[ERROR] ファイル読み込みエラー: {e}")
        logger.error(f"DOCXファイル読み込みエラー: {docx_file} - {e}")
        return image_names

    print("=== テーブル読み込み開始 ===")

    for table_index, table in enumerate(doc.tables, start=1):
        left_text = table.rows[0].cells[0].text.strip().replace("\n", "") if len(table.rows) > 0 else ""
        print(f"[テーブル{table_index}] 左セル: {left_text}")

        for row_index, row in enumerate(table.rows, start=1):
            right_text = row.cells[1].text if len(row.cells) > 1 else ""
            for line in right_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                print(f"  行{row_index} 右セル: {line}")

                matches = re.findall(config.IMAGE_PATTERN, line)
                if matches:
                    print(f"    マッチ: {matches}")

                for match in matches:
                    # matchはタプルなので、空でない最初の要素を取得
                    image_name = next((m for m in match if m), "").strip()
                    if image_name:  # 空でない場合のみ追加
                        image_names.append({
                            "file_name": file_name,
                            "output_dir": output_dir,
                            "row_index": left_text,
                            "image_name": image_name
                        })

    # THUMBNAILの画像名を追加
    if image_names:
        print("=== THUMBNAILの画像名追加処理開始 ===")
        # image_namesの中から "-kv" または "_kv" を含む画像名を抽出し、
        # "kv" を "thumbnail" に置換した画像名を image_names に追加
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
            if image_utils.find_input_image(new_name):
                additional_matches.append(new_name)

        if additional_matches:
            print(f"追加された画像名: {additional_matches}")
            logger.info(f"追加された画像名: {additional_matches}")

            # image_namesに追加
            for thumbnail_name in additional_matches:
                image_names.append({
                    "file_name": file_name,
                    "output_dir": output_dir,
                    "row_index": "THUMBNAIL",
                    "image_name": thumbnail_name.strip()
                })

    print("=== 正規表現抽出完了 ===")
    print(f"抽出された画像名数: {len(image_names)}")
    logger.info(f"画像名抽出完了: {file_name} - 抽出数: {len(image_names)}")

    return image_names


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
    logger = logging.getLogger(__name__)
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
