"""
メイン処理
DOCXファイルから画像名を抽出し、WebP形式に変換する
"""

import os
import json
import re
import glob
import logging
from typing import List, Dict
import shutil

import config
import docx_parser
import image_utils


def setup_logging():
    """
    ログ設定を初期化
    """
    # ログディレクトリを作成
    # すでにディレクトリが存在していたら削除
    if os.path.exists(config.LOG_DIR):
        shutil.rmtree(config.LOG_DIR)
    os.makedirs(config.LOG_DIR, exist_ok=True)

    # ログファイルのパス
    log_file_path = os.path.join(config.LOG_DIR, config.LOG_FILE)

    # ログ設定
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()  # コンソールにも出力
        ]
    )

    # ロガーを取得
    logger = logging.getLogger(__name__)
    logger.info("ログ設定を初期化しました")
    return logger


def process_single_file(docx_file: str, file_index: int, total_files: int) -> List[str]:
    """
    単一のDOCXファイルを処理

    Args:
        docx_file: DOCXファイルのパス
        file_index: ファイルのインデックス（1から開始）
        total_files: 総ファイル数

    Returns:
        変換された画像ファイルのパスのリスト
    """
    logger = logging.getLogger(__name__)
    file_name = os.path.basename(docx_file)
    file_name_without_ext = os.path.splitext(file_name)[0]
    output_dir = f"{config.OUTPUT_BASE_DIR}/{file_name_without_ext}"

    print(f"\n=== ファイル {file_index}/{total_files}: {file_name} ===")
    print(f"出力ディレクトリ: {output_dir}")
    logger.info(f"ファイル処理開始: {file_name} (出力ディレクトリ: {output_dir})")

    # 出力ディレクトリが既に存在する場合はスキップ
    if os.path.exists(output_dir):
        print(f"[SKIP] 出力ディレクトリが既に存在するため、{file_name} の処理をスキップします")
        logger.info(f"スキップ: {file_name} - 出力ディレクトリが既に存在")
        return []

    # ファイル専用の出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)

    # DOCXから画像名抽出
    image_names = docx_parser.extract_image_names_from_docx(docx_file)

    # 画像変換処理
    print("=== 画像変換処理開始 ===")
    converted_images = []

    for record in image_names:
        row_text = record["row_index"]
        image_name = record["image_name"]
        output_dir = record["output_dir"]

        print(f"処理対象: row_index={row_text}, image_name={image_name}")

        # コード抽出
        match = re.match(config.CODE_PATTERN, row_text)
        if not match:
            print(f"  [WARN] コード抽出失敗: {row_text}")
            logger.warning(f"コード抽出失敗: {row_text}")
            continue

        key = match.group(1)
        if key not in config.WIDTH_MAP:
            print(f"  [WARN] {key} の幅未定義。スキップ: {image_name}")
            logger.warning(f"幅未定義: {key} - スキップ: {image_name}")
            continue

        sizes = config.WIDTH_MAP[key]

        # 入力ファイル確認
        input_file = image_utils.find_input_image(image_name)
        if not input_file:
            print(f"  [ERROR] 入力ファイルが存在しません: {image_name} (jpg/png/webp)")
            logger.error(f"入力ファイルが存在しません: {image_name}")
            continue

        print(f"  入力ファイル発見: {input_file}")

        # 幅ごとにWebP変換（元画像がWebPの場合はリサイズのみ）
        for size in sizes:
            output_file = f"{output_dir}/{image_name}{size[0]}.webp"
            print(f"  → 変換開始: {input_file} → {output_file} (width={size[0]} height={size[1]})")

            # Pillowを使用して変換（WebP形式の場合はリサイズのみ）
            success = image_utils.convert_image_with_pillow(input_file, size, output_file)

            if success:
                print(f"    [OK] {image_name} を {size}px 幅で WebP に変換成功")
                logger.info(f"変換成功: {image_name} - {size}px")
                converted_images.append(f"{output_dir}/{image_name}{size[0]}.webp")
            else:
                print(f"    [NG] {image_name} の変換失敗 ({size}px)")
                logger.error(f"変換失敗: {image_name} - {size}px")

    print(f"=== ファイル {file_name} 処理完了 ===")
    logger.info(f"ファイル処理完了: {file_name} - 変換画像数: {len(converted_images)}")
    return converted_images


def save_results(all_image_names: List[Dict[str, str]], all_converted_images: List[str]):
    """
    処理結果をファイルに保存

    Args:
        all_image_names: 全ファイルの画像名情報
        all_converted_images: 変換された画像ファイルのパス一覧
    """
    # 全ファイルの結果をJSON出力
    json_file = "all_image_names.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_image_names, f, ensure_ascii=False, indent=2)
    print(f"全ファイルの画像名JSON出力完了: {json_file}")

    # 変換成功画像の一覧をファイル出力
    list_file = "all_converted_images.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        f.write("\n".join(all_converted_images))

    print(f"全ファイルの変換済み画像一覧を {list_file} に出力しました。")
    print(f"総変換画像数: {len(all_converted_images)}")


def display_output_structure(docx_files: List[str]):
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


def main():
    """メイン処理"""
    # ログ設定を初期化
    logger = setup_logging()
    logger.info("=== 画像変換処理開始 ===")

    # DOCXファイル一覧取得
    docx_files = docx_parser.get_docx_files()

    # ファイル存在確認
    if not docx_parser.validate_docx_files(docx_files):
        logger.error("DOCXファイルの検証に失敗しました")
        exit(1)

    # 出力ディレクトリ（ベース）を作成
    os.makedirs(config.OUTPUT_BASE_DIR, exist_ok=True)

    # 全ファイル処理
    all_converted_images = []
    all_image_names = []

    for file_index, docx_file in enumerate(docx_files, start=1):
        # 単一ファイル処理
        converted_images = process_single_file(docx_file, file_index, len(docx_files))
        if converted_images == []:
            continue

        all_converted_images.extend(converted_images)

        # 画像名情報を取得（スキップされたファイルも含む）
        image_names = docx_parser.extract_image_names_from_docx(docx_file)
        all_image_names.extend(image_names)

    print("\n=== 全ファイル処理完了 ===")
    logger.info(f"全ファイル処理完了 - 総変換画像数: {len(all_converted_images)}")

    # 結果保存
    save_results(all_image_names, all_converted_images)

    # 出力構造表示
    display_output_structure(docx_files)

    logger.info("=== 画像変換処理終了 ===")


if __name__ == "__main__":
    main()