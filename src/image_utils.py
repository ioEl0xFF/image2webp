"""
画像処理ユーティリティ
画像の読み込み、リサイズ、WebP変換に関する機能を提供
"""

from PIL import Image, ImageOps
from typing import List, Tuple
import logging
from . import config


def has_alpha(img: Image.Image) -> bool:
    """画像にアルファチャンネルがあるかチェック"""
    return img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)


def load_image_with_exif(path: str) -> Image.Image:
    """EXIF情報を考慮して画像を読み込み"""
    img = Image.open(path)
    # EXIFの向きを自動適用
    img = ImageOps.exif_transpose(img)
    return img


def resize_fit(img: Image.Image, size: List[int]) -> Image.Image:
    """
    リサイズし、余白を追加して target サイズに収める

    Args:
        img: 元画像
        size: [幅, 高さ] のリスト。高さが0の場合は元画像のアスペクト比に合わせる

    Returns:
        リサイズされた画像
    """
    # 元画像のアスペクト比とターゲットサイズのアスペクト比を比較
    src_w, src_h = img.size
    target_w, target_h = size

    # heightが0の場合、元の画像のアスペクト比に合わせる
    if size[1] == 0:
        target_h = int(target_w * src_h / src_w)

    # 元画像とターゲットサイズのアスペクト比が同じだったらそのままリサイズ
    elif src_w / src_h == target_w / target_h:
        return img.resize((target_w, target_h), 1)

    # 元画像とターゲットサイズのアスペクト比が異なる場合、余白を追加してリサイズ
    elif src_w / src_h > target_w / target_h:
        # 元画像のアスペクト比がターゲットサイズのアスペクト比より大きい場合
        new_w = target_w
        new_h = int(new_w * src_h / src_w)
    else:
        # 元画像のアスペクト比がターゲットサイズのアスペクト比より小さい場合
        new_h = target_h
        new_w = int(new_h * src_w / src_h)

    img_resized = img.resize((new_w, new_h), 1)

    # 余白を追加してターゲットサイズに合わせる
    # ターゲットサイズのアスペクト比が1:1の場合、透過で余白を追加
    if target_w / target_h == 1:
        result = Image.new("RGBA", (target_w, target_h), (255, 255, 255, 0))
    else:
        result = Image.new("RGBA", (target_w, target_h), (255, 255, 255, 255))

    # 中央に配置
    left = (target_w - new_w) // 2
    top = (target_h - new_h) // 2
    result.paste(img_resized, (left, top))

    return result


def ensure_rgba_or_rgb(img: Image.Image) -> Image.Image:
    """WEBP保存時に最適なモードへ変換"""
    if has_alpha(img):
        return img.convert("RGBA")
    else:
        return img.convert("RGB")


def save_webp(img: Image.Image, dst_path: str):
    """WEBP形式で保存"""
    img.save(
        dst_path,
        format="WEBP",
        quality=config.WEBP_QUALITY,    # 画質（0-100）
        method=config.WEBP_METHOD,      # 圧縮アルゴ（0-6 高いほど時間↑/サイズ↓）
        lossless=config.WEBP_LOSSLESS,  # 可逆にしたい場合 True
    )


def is_webp_image(input_path: str) -> bool:
    """
    入力画像がWebP形式かどうかを判定

    Args:
        input_path: 入力画像のパス

    Returns:
        WebP形式の場合True、そうでなければFalse
    """
    try:
        with Image.open(input_path) as img:
            return img.format == 'WEBP'
    except Exception:
        return False


def convert_image_with_pillow(input_path: str, size: List[int], output_path: str) -> bool:
    """
    Pillowを使用して画像を変換
    元画像がWebP形式の場合はリサイズのみ行う

    Args:
        input_path: 入力画像のパス
        size: [幅, 高さ] のリスト
        output_path: 出力画像のパス

    Returns:
        変換成功時True、失敗時False
    """
    try:
        # 画像読み込み
        img = load_image_with_exif(input_path)

        # 元画像がWebP形式かどうかを判定
        is_webp = is_webp_image(input_path)

        if is_webp:
            print(f"    [INFO] 元画像がWebP形式のため、リサイズのみ実行")
            # WebP形式の場合はリサイズのみ
            resized_img = resize_fit(img, size)
            # そのままWebP形式で保存
            save_webp(resized_img, output_path)
        else:
            print(f"    [INFO] 元画像をWebP形式に変換してリサイズ実行")
            # 他の形式の場合は従来通り変換
            img = ensure_rgba_or_rgb(img)
            # リサイズ（余白追加）
            resized_img = resize_fit(img, size)
            # WEBP保存
            save_webp(resized_img, output_path)

        return True
    except Exception as e:
        logger = logging.getLogger(__name__)
        print(f"    [ERROR] Pillow変換エラー: {e}")
        logger.error(f"画像変換エラー: {input_path} → {output_path} - {e}")
        return False


def find_input_image(image_name: str) -> str:
    """
    指定された画像名に対応する入力ファイルを検索

    Args:
        image_name: 画像名（拡張子なし）

    Returns:
        見つかったファイルのパス、見つからない場合はNone
    """
    import os
    for ext in config.SUPPORTED_EXTENSIONS:
        candidate = f"{config.IMAGES_DIR}/{image_name}.{ext}"
        if os.path.exists(candidate):
            return candidate
    return None
