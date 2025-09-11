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

    # 存在しない画像記録ファイルを初期化（空ファイルを作成）
    missing_images_file = os.path.join(config.LOG_DIR, "missing_images.txt")
    try:
        with open(missing_images_file, "w", encoding="utf-8") as f:
            f.write("# 存在しない画像ファイル一覧\n")
            f.write("# 形式: DOCXファイル名: 画像名\n\n")
        logger.info("存在しない画像記録ファイルを初期化しました")
    except Exception as e:
        logger.error(f"存在しない画像記録ファイルの初期化に失敗: {e}")

    return logger


def extract_code_from_row_index(row_index: str, logger) -> str:
    """
    row_indexからコード部分を抽出する

    Args:
        row_index: 行インデックス（左セルのテキスト）
        logger: ロガー

    Returns:
        抽出されたコード（抽出失敗時はNone）
    """
    code_match = re.match(config.CODE_PATTERN, row_index)
    if not code_match:
        print(f"  [WARN] コード抽出失敗: {row_index}")
        logger.warning(f"コード抽出失敗: {row_index}")
        return None

    return code_match.group(1)


def record_missing_image(image_name: str, docx_file_name: str, logger) -> None:
    """
    存在しない画像名をファイルに記録する

    Args:
        image_name: 存在しない画像名
        docx_file_name: DOCXファイル名（拡張子なし）
        logger: ロガー
    """
    missing_images_file = os.path.join(config.LOG_DIR, "missing_images.txt")

    try:
        # ファイルに追記（存在しない場合は新規作成）
        with open(missing_images_file, "a", encoding="utf-8") as f:
            f.write(f"{docx_file_name}: {image_name}\n")

        logger.info(f"存在しない画像を記録: {image_name} (ファイル: {docx_file_name})")
    except Exception as e:
        logger.error(f"存在しない画像の記録に失敗: {image_name} - {e}")


def replace_html_image_names(html_content: str, image_names: List[Dict[str, str]], html_file_path: str, logger) -> str:
    """
    HTMLファイル内の画像名を置き換える

    Args:
        html_content: HTMLファイルの内容
        image_names: 画像名情報のリスト
        html_file_path: HTMLファイルのパス
        logger: ロガー

    Returns:
        置き換え後のHTMLコンテンツ
    """
    print("=== HTML画像名置き換え処理実行 ===")

    # 各行の画像名ごとに処理
    for record in image_names:
        row_index = record["row_index"]
        image_name = record["image_name"]

        print(f"処理対象: row_index={row_index}, image_name={image_name}")

        # row_indexからコード部分を抽出
        code = extract_code_from_row_index(row_index, logger)
        if not code:
            continue

        # 抽出したコードからHTML_IMAGE_REPLACE_ORDERの要素を取得
        if code not in config.HTML_IMAGE_REPLACE_ORDER:
            print(f"  [WARN] {code} の置き換え順が未定義。スキップ: {image_name}")
            logger.warning(f"置き換え順未定義: {code} - スキップ: {image_name}")
            continue

        replace_order = config.HTML_IMAGE_REPLACE_ORDER[code]
        print(f"  置き換え順: {replace_order}")

        # HTMLファイル内でimage_nameと一致するファイル名を検索・置換
        current_content = html_content
        search_start = 0

        for i, size in enumerate(replace_order):
            # 検索パターン: 画像名 + 拡張子（jpg, png, webp等）
            pattern = rf'\b{re.escape(image_name)}\.(jpg|jpeg|png|webp|JPG|JPEG|PNG|WEBP)\b'

            # 現在の位置から検索
            match = re.search(pattern, current_content[search_start:], re.IGNORECASE)

            if match:
                # マッチした位置を全体の位置に変換
                match_start = search_start + match.start()
                match_end = search_start + match.end()

                # 置換後のファイル名
                new_filename = f"{image_name}{size}.webp"

                print(f"    置換 {i+1}/{len(replace_order)}: {match.group()} → {new_filename}")
                logger.info(f"HTML画像名置換: {match.group()} → {new_filename}")

                # 置換実行
                current_content = current_content[:match_start] + new_filename + current_content[match_end:]

                # 次の検索開始位置を更新（置換後の位置から）
                search_start = match_start + len(new_filename)
            else:
                print(f"    [WARN] 置換 {i+1}/{len(replace_order)}: {image_name} のマッチが見つかりません")
                logger.warning(f"HTML画像名マッチなし: {image_name} (置換 {i+1}/{len(replace_order)})")

        html_content = current_content

    # 置換後のHTMLファイルを保存
    try:
        with open(html_file_path, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)
        print(f"HTMLファイル更新完了: {html_file_path}")
        logger.info(f"HTMLファイル更新完了: {html_file_path}")
    except Exception as e:
        print(f"[ERROR] HTMLファイルの保存に失敗しました: {html_file_path} ({e})")
        logger.error(f"HTMLファイル保存失敗: {html_file_path} ({e})")

    return html_content


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

    # DOCXから画像名抽出
    image_names = docx_parser.extract_image_names_from_docx(docx_file)

    # HTML画像名置き換え処理
    # HTML_DIRにファイル名と同じ名前のHTMLファイルがあれば、そのhtmlファイルを読み込む
    html_file_path = os.path.join(config.HTML_DIR, f"{file_name_without_ext}.html")
    html_content = None

    if os.path.exists(html_file_path):
        print(f"HTMLファイル発見: {html_file_path} を読み込みます")
        logger.info(f"HTMLファイル発見: {html_file_path} を読み込み")
        try:
            with open(html_file_path, "r", encoding="utf-8") as html_file:
                html_content = html_file.read()
        except Exception as e:
            print(f"[ERROR] HTMLファイルの読み込みに失敗しました: {html_file_path} ({e})")
            logger.error(f"HTMLファイルの読み込み失敗: {html_file_path} ({e})")
    else:
        print(f"HTMLファイル未発見: {html_file_path}")
        logger.info(f"HTMLファイル未発見: {html_file_path}")

    # HTML画像名置き換え処理実行
    if html_content and image_names:
        print("=== HTML画像名置き換え処理開始 ===")
        html_content = replace_html_image_names(html_content, image_names, html_file_path, logger)


    # 画像変換処理
    print("=== 画像変換処理開始 ===")

    # ファイル専用の出力ディレクトリを作成します。
    os.makedirs(output_dir, exist_ok=True)

    converted_images = []

    for record in image_names:
        row_text = record["row_index"]
        image_name = record["image_name"]
        output_dir = record["output_dir"]

        print(f"処理対象: row_index={row_text}, image_name={image_name}")

        # コード抽出
        key = extract_code_from_row_index(row_text, logger)
        if not key:
            continue
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
            # 存在しない画像名をファイルに記録
            record_missing_image(image_name, file_name_without_ext, logger)
            continue

        print(f"  入力ファイル発見: {input_file}")

        # 幅ごとにWebP変換（元画像がWebPの場合はリサイズのみ）
        for size in sizes:
            output_file = f"{output_dir}/{image_name}{size[0]}.webp"

            # 出力ファイルが既に存在する場合はスキップ
            if os.path.exists(output_file):
                print(f"  → 出力ファイルが既に存在するため、{image_name} を {size}px 幅で WebP に変換しません")
                logger.info(f"スキップ: {image_name} - {size}px - 出力ファイルが既に存在")
                continue

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
    # 全ファイルの結果をJSON出力（ログディレクトリに保存）
    json_file = os.path.join(config.LOG_DIR, "all_image_names.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_image_names, f, ensure_ascii=False, indent=2)
    print(f"全ファイルの画像名JSON出力完了: {json_file}")

    # 変換成功画像の一覧をファイル出力（ログディレクトリに保存）
    list_file = os.path.join(config.LOG_DIR, "all_converted_images.txt")
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

    # 存在しない画像の件数を表示
    missing_images_file = os.path.join(config.LOG_DIR, "missing_images.txt")
    if os.path.exists(missing_images_file):
        try:
            with open(missing_images_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # コメント行を除く
                missing_count = len([line for line in lines if not line.strip().startswith("#") and line.strip()])
                if missing_count > 0:
                    print(f"存在しない画像ファイル数: {missing_count}")
                    print(f"詳細は {missing_images_file} を確認してください")
                    logger.info(f"存在しない画像ファイル数: {missing_count}")
        except Exception as e:
            logger.error(f"存在しない画像ファイル数の取得に失敗: {e}")

    # 結果保存
    save_results(all_image_names, all_converted_images)

    # 出力構造表示
    display_output_structure(docx_files)

    logger.info("=== 画像変換処理終了 ===")


if __name__ == "__main__":
    main()