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


def get_image_size_from_media_query(media_query: str, code: str, tag_type: str = "source", html_context: str = "", html_content: str = "", tag_position: int = 0) -> int:
    """
    メディアクエリから適切な画像サイズを取得する（クラス名考慮）

    Args:
        media_query: メディアクエリ文字列
        code: コード（COMFRPTC12など）
        tag_type: タグの種類（"source" または "img"）
        html_context: HTMLコンテキスト（クラス名など）
        html_content: HTMLファイルの内容（COMFRPTC12のカーセル判定用）
        tag_position: タグの位置（COMFRPTC12のカーセル判定用）

    Returns:
        画像サイズ（ピクセル）
    """
    if code not in config.MIN_WIDTH_SIZE_MAP:
        return None

    size_map = config.MIN_WIDTH_SIZE_MAP[code]

    # メディアクエリからmin-widthの値を抽出
    width_match = re.search(r'\(min-width:\s*(\d+)px\)', media_query)
    if not width_match:
        # メディアクエリがない場合はデフォルトサイズを返す
        default_key = f"{tag_type}_default"
        return size_map.get(default_key, 500)

    width = int(width_match.group(1))

    # 解像度条件をチェック
    has_2dppx = 'min-resolution:2dppx' in media_query

    # 複数サイズ対応の場合は、解像度条件とクラス名に応じて選択
    if width in size_map:
        size_value = size_map[width]

        if isinstance(size_value, list):
            # 複数サイズがある場合
            if has_2dppx:
                # 高解像度の場合
                if code == "COMFRPTC12" and (width == 1562 or width == 1041):
                    # COMFRPTC12の1562pxまたは1041pxの特別処理
                    if html_content and tag_position > 0:
                        # 新しいカーセル判定ロジックを使用
                        is_carousel = is_carousel_for_comfrptc12(html_content, tag_position)
                    else:
                        # フォールバック: 従来の方法
                        is_carousel = "_carousel" in html_context

                    if is_carousel:
                        # カルーセルの場合は大きいサイズ（1800または1200）
                        return max(size_value)
                    else:
                        # 通常表示の場合は小さいサイズ（900）
                        return min(size_value)
                else:
                    # その他の場合は大きいサイズを選択
                    return max(size_value)
            else:
                # 通常解像度の場合は小さいサイズを選択
                return min(size_value)
        else:
            # 単一サイズの場合
            return size_value

    # COMFRPTC23の特別処理：min-widthがない場合の判別
    if code == "COMFRPTC23" and not width_match:
        if has_2dppx:
            # (min-resolution: 2dppx) のみの場合 → 240
            return 240
        else:
            # 条件なしの場合 → 120
            return 120

    # 該当するmin-widthがない場合はデフォルトサイズを返す
    default_key = f"{tag_type}_default"
    return size_map.get(default_key, 500)


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

        # メディアクエリ置換が可能な場合は実行
        if code in config.MIN_WIDTH_SIZE_MAP:
            print(f"  {code}のメディアクエリベース置換を実行")
            html_content = replace_html_image_names_by_media_query(html_content, image_name, code, logger)
        else:
            print(f"  {code}のメディアクエリベース置換を実行できません。スキップ: {image_name}")
            logger.warning(f"メディアクエリベース置換できません: {code} - スキップ: {image_name}")
            continue


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


def get_html_context_for_image(html_content: str, image_name: str, tag_position: int) -> str:
    """
    画像タグの周辺のHTMLコンテキスト（クラス名など）を取得する

    Args:
        html_content: HTMLファイルの内容
        image_name: 画像名
        tag_position: タグの位置

    Returns:
        HTMLコンテキスト文字列
    """
    # タグの前後200文字を取得してコンテキストを分析
    start = max(0, tag_position - 200)
    end = min(len(html_content), tag_position + 200)
    context = html_content[start:end]

    return context


def is_carousel_for_comfrptc12(html_content: str, tag_position: int) -> bool:
    """
    COMFRPTC12専用のカーセル判定を行う

    Args:
        html_content: HTMLファイルの内容
        tag_position: タグの位置

    Returns:
        True: カーセル版, False: 通常版
    """
    # ファイル名が見つかった行から上に順番に探索
    lines = html_content[:tag_position].split('\n')

    # 後ろから50行まで探索
    search_lines = lines[-50:] if len(lines) >= 50 else lines

    for line in reversed(search_lines):
        # "_carousel"が見つかった場合はカーセル版
        if "_carousel" in line:
            return True
        # "mCommonsectionImgitem"が見つかった場合は通常版
        if "mCommonsectionImgitem" in line:
            return False

    # 50行探しても見つからない場合は通常版
    return False


def replace_html_image_names_by_media_query(html_content: str, image_name: str, code: str, logger) -> str:
    """
    メディアクエリに基づいてHTMLファイル内の画像名を置き換える（クラス名考慮）

    Args:
        html_content: HTMLファイルの内容
        image_name: 画像名
        code: コード（COMFRPTC12など）
        logger: ロガー

    Returns:
        置き換え後のHTMLコンテンツ
    """
    # <source>タグのパターンを検索
    source_pattern = rf'<source[^>]*data-srcset="[^"]*{re.escape(image_name)}[^"]*"[^>]*>'

    # 各<source>タグを処理
    def replace_source_tag(match):
        source_tag = match.group(0)
        tag_position = match.start()

        # HTMLコンテキストを取得
        html_context = get_html_context_for_image(html_content, image_name, tag_position)

        # メディアクエリを抽出
        media_match = re.search(r'media="([^"]*)"', source_tag)
        if not media_match:
            print(f"    [INFO] メディアクエリが見つかりません。source_defaultを適用: {source_tag[:100]}...")
            # メディアクエリがない場合はsource_defaultを使用
            media_query = ""
        else:
            media_query = media_match.group(1)

        # 適切な画像サイズを取得（sourceタグ用 + HTMLコンテキスト考慮）
        size = get_image_size_from_media_query(media_query, code, "source", html_context, html_content, tag_position)
        if not size:
            print(f"    [WARN] サイズが決定できません: {media_query}")
            return source_tag

        # 画像ファイル名を置換
        new_filename = f"{image_name}{size}.webp"
        new_source_tag = re.sub(
            rf'{re.escape(image_name)}[^"]*\.(jpg|jpeg|png|webp|JPG|JPEG|PNG|WEBP)',
            new_filename,
            source_tag,
            flags=re.IGNORECASE
        )

        # COMFRPTC12とCOMFRPTC23の特別な判別理由を追加
        reason_info = ""
        if code == "COMFRPTC12":
            # メディアクエリからmin-widthの値を再抽出
            width_match_log = re.search(r'\(min-width:\s*(\d+)px\)', media_query)
            has_2dppx_log = 'min-resolution:2dppx' in media_query

            if width_match_log and has_2dppx_log:
                width_log = int(width_match_log.group(1))
                is_carousel_log = is_carousel_for_comfrptc12(html_content, tag_position)
                if width_log == 1562:
                    if is_carousel_log:
                        reason_info = " (カルーセル1800)"
                    else:
                        reason_info = " (通常表示900)"
                elif width_log == 1041:
                    if is_carousel_log:
                        reason_info = " (カルーセル1200)"
                    else:
                        reason_info = " (通常表示900)"
        elif code == "COMFRPTC23":
            # メディアクエリからmin-widthの値を再抽出
            width_match_log = re.search(r'\(min-width:\s*(\d+)px\)', media_query)
            has_2dppx_log = 'min-resolution:2dppx' in media_query

            if not width_match_log:
                if has_2dppx_log:
                    reason_info = " (解像度のみ240)"
                else:
                    reason_info = " (条件なし120)"
            elif width_match_log and int(width_match_log.group(1)) == 1440 and has_2dppx_log:
                reason_info = " (1440px+2dppx360)"

        print(f"    メディアクエリ置換: {media_query} → {new_filename}{reason_info}")
        logger.info(f"メディアクエリ置換: {media_query} → {new_filename}{reason_info}")

        return new_source_tag

    # <source>タグを置換
    html_content = re.sub(source_pattern, replace_source_tag, html_content, flags=re.IGNORECASE)

    # <img>タグも処理
    img_pattern = rf'<img[^>]*data-src="[^"]*{re.escape(image_name)}[^"]*"[^>]*>'

    def replace_img_tag(match):
        img_tag = match.group(0)
        tag_position = match.start()

        # HTMLコンテキストを取得
        html_context = get_html_context_for_image(html_content, image_name, tag_position)

        # imgタグ用のデフォルトサイズを取得
        default_size = get_image_size_from_media_query("", code, "img", html_context)
        new_filename = f"{image_name}{default_size}.webp"

        new_img_tag = re.sub(
            rf'{re.escape(image_name)}[^"]*\.(jpg|jpeg|png|webp|JPG|JPEG|PNG|WEBP)',
            new_filename,
            img_tag,
            flags=re.IGNORECASE
        )

        print(f"    IMGタグ置換: → {new_filename}")
        logger.info(f"IMGタグ置換: → {new_filename}")

        return new_img_tag

    # <img>タグを置換
    html_content = re.sub(img_pattern, replace_img_tag, html_content, flags=re.IGNORECASE)

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