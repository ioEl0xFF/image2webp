"""
設定ファイル
JSONベースの設定管理システムを使用して、画像変換処理で使用する定数やマッピングを定義
"""

import re
from .config_loader import config_loader

# JSONから設定値を読み込み、モジュール変数として公開

# ディレクトリ設定
DOCX_DIRECTORY = config_loader.get("directories.docx_directory", "docxs")
OUTPUT_BASE_DIR = config_loader.get("directories.output_base_dir", "output")
IMAGES_DIR = config_loader.get("directories.images_dir", "images")
HTML_DIR = config_loader.get("directories.html_dir", "html")

# 正規表現パターン
IMAGE_PATTERN = config_loader.get("patterns.image_pattern", 
    r"(?:[＜<〈]画像(?:名|\d*)?(?:（[^）]*）)?[＞>〉]\s*([a-zA-Z0-9\-_]+)|画像名[:：]\s*([a-zA-Z0-9\-_]+))")
CODE_PATTERN = config_loader.get("patterns.code_pattern", r"^(COMFRPTC\d+|GSTFRPTA\d+|THUMBNAIL)")

# 左セルコードと幅の対応
WIDTH_MAP = config_loader.get_width_map()

# min-widthとサイズのマッピング（文字列キーを整数に変換）
_min_width_map = config_loader.get_min_width_size_map()
MIN_WIDTH_SIZE_MAP = {}
for code, mapping in _min_width_map.items():
    MIN_WIDTH_SIZE_MAP[code] = {}
    for key, value in mapping.items():
        if key in ["source_default", "img_default"]:
            MIN_WIDTH_SIZE_MAP[code][key] = value
        else:
            # 文字列キーを整数に変換
            try:
                int_key = int(key)
                MIN_WIDTH_SIZE_MAP[code][int_key] = value
            except ValueError:
                MIN_WIDTH_SIZE_MAP[code][key] = value

# 確認する拡張子
SUPPORTED_EXTENSIONS = config_loader.get("image_processing.supported_extensions", 
    ["webp", "WEBP", "jpg", "png", "JPG", "PNG"])

# WebP保存設定
WEBP_QUALITY = config_loader.get("image_processing.webp_quality", 100)
WEBP_METHOD = config_loader.get("image_processing.webp_method", 6)
WEBP_LOSSLESS = config_loader.get("image_processing.webp_lossless", True)

# ログ設定
LOG_DIR = config_loader.get("directories.log_dir", ".logs")
LOG_FILE = config_loader.get("logging.log_file", "LOG.log")
LOG_LEVEL = config_loader.get("logging.log_level", "INFO")
LOG_FORMAT = config_loader.get("logging.log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_DATE_FORMAT = config_loader.get("logging.log_date_format", "%Y-%m-%d %H:%M:%S")


def reload_config():
    """
    設定を再読み込みしてモジュール変数を更新
    GUI設定画面などから呼び出される
    """
    global DOCX_DIRECTORY, OUTPUT_BASE_DIR, IMAGES_DIR, HTML_DIR
    global IMAGE_PATTERN, CODE_PATTERN, WIDTH_MAP, MIN_WIDTH_SIZE_MAP
    global SUPPORTED_EXTENSIONS, WEBP_QUALITY, WEBP_METHOD, WEBP_LOSSLESS
    global LOG_DIR, LOG_FILE, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT
    
    # 設定を再読み込み
    config_loader.reload_config()
    
    # モジュール変数を更新
    DOCX_DIRECTORY = config_loader.get("directories.docx_directory", "docxs")
    OUTPUT_BASE_DIR = config_loader.get("directories.output_base_dir", "output")
    IMAGES_DIR = config_loader.get("directories.images_dir", "images")
    HTML_DIR = config_loader.get("directories.html_dir", "html")
    
    IMAGE_PATTERN = config_loader.get("patterns.image_pattern", 
        r"(?:[＜<〈]画像(?:名|\d*)?(?:（[^）]*）)?[＞>〉]\s*([a-zA-Z0-9\-_]+)|画像名[:：]\s*([a-zA-Z0-9\-_]+))")
    CODE_PATTERN = config_loader.get("patterns.code_pattern", r"^(COMFRPTC\d+|GSTFRPTA\d+|THUMBNAIL)")
    
    WIDTH_MAP = config_loader.get_width_map()
    
    # MIN_WIDTH_SIZE_MAPの更新
    _min_width_map = config_loader.get_min_width_size_map()
    MIN_WIDTH_SIZE_MAP = {}
    for code, mapping in _min_width_map.items():
        MIN_WIDTH_SIZE_MAP[code] = {}
        for key, value in mapping.items():
            if key in ["source_default", "img_default"]:
                MIN_WIDTH_SIZE_MAP[code][key] = value
            else:
                try:
                    int_key = int(key)
                    MIN_WIDTH_SIZE_MAP[code][int_key] = value
                except ValueError:
                    MIN_WIDTH_SIZE_MAP[code][key] = value
    
    SUPPORTED_EXTENSIONS = config_loader.get("image_processing.supported_extensions", 
        ["webp", "WEBP", "jpg", "png", "JPG", "PNG"])
    
    WEBP_QUALITY = config_loader.get("image_processing.webp_quality", 100)
    WEBP_METHOD = config_loader.get("image_processing.webp_method", 6)
    WEBP_LOSSLESS = config_loader.get("image_processing.webp_lossless", True)
    
    LOG_DIR = config_loader.get("directories.log_dir", ".logs")
    LOG_FILE = config_loader.get("logging.log_file", "LOG.log")
    LOG_LEVEL = config_loader.get("logging.log_level", "INFO")
    LOG_FORMAT = config_loader.get("logging.log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_DATE_FORMAT = config_loader.get("logging.log_date_format", "%Y-%m-%d %H:%M:%S")