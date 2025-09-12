"""
設定ファイル
画像変換処理で使用する定数やマッピングを定義
"""

import re

# ディレクトリ設定
DOCX_DIRECTORY = "docxs"
OUTPUT_BASE_DIR = "output"
IMAGES_DIR = "images"
HTML_DIR = "html"

# 正規表現パターン
#
# ＜画像＞や＜画像名＞などの全角表記に加え、「画像名：sample-image-01」のような半角コロン区切り表記にも対応します。
# 例: ＜画像＞sample-image-01
#     ＜画像名＞sample-image-02
#     画像名：sample-image-03
#     画像名:sample-image-04
#
# - ＜画像...＞パターン: 従来通り全角括弧・補足も対応
# - 画像名：...パターン: 「画像名：」または「画像名:」の直後に画像名（英数字・ハイフン・アンダースコア）を抽出
#
# どちらにもマッチするように正規表現を拡張しています。
IMAGE_PATTERN = (
    r"(?:"
    r"[＜<〈]画像(?:名|\d*)?(?:（[^）]*）)?[＞>〉]\s*([a-zA-Z0-9\-_]+)"  # ＜画像＞系
    r"|"
    r"画像名[:：]\s*([a-zA-Z0-9\-_]+)"                      # 画像名：系（全角・半角コロン両対応）
    r")"
)

# コード抽出正規表現（GSTにも対応）
CODE_PATTERN = r"^(COMFRPTC\d+|GSTFRPTA\d+|THUMBNAIL)"

# 左セルコードと幅の対応
WIDTH_MAP = {
    "COMFRPTC09": [[1800, 1200], [1200, 800], [900, 600], [500, 333]],
    "COMFRPTC12": [[1800, 1200], [1200, 800], [900, 600], [500, 333]],
    "COMFRPTC14": [[800, 800], [600, 600], [400, 400]],
    "COMFRPTC13": [[1200, 900], [900, 600], [500, 333]],
    "COMFRPTC34": [[1800, 1200], [1200, 800], [900, 600], [500, 333]],
    "COMFRPTC15": [[300, 300], [150, 150]],
    "COMFRPTC23": [[360, 360], [240, 240], [120, 120]],
    "COMFRPTC17": [[900, 600], [500, 333]],
    "COMFRPTC21": [[900, 900], [500, 500]],
    "GSTFRPTA15": [[900, 0], [500, 0]],
    "COMFRPTC03": [[900, 0], [500, 0]],
    "COMFRPTC30": [[900, 600], [500, 333]],
    "THUMBNAIL" : [[900, 600], [500, 333]],
}

# min-widthとサイズのマッピング
MIN_WIDTH_SIZE_MAP = {
    "COMFRPTC09": {
        2082: 900,
        1562: 1800,
        1388: 1200,
        1041: 1200,
        781: 900,
        768: 500,
        "source_default": 900,
        "img_default": 900
    },
    "COMFRPTC12": {
        1562: [1800, 900],  # 複数サイズ対応
        1388: 1200,
        1041: [1200, 900],  # 複数サイズ対応
        781: 900,
        768: 500,
        "source_default": 900,
        "img_default": 500
    },
    "COMFRPTC14": {
        1388: 800,
        1041: 600,
        "source_default": 400,
        "img_default": 400
    },
    "COMFRPTC13": {
        1388: 1200,
        1041: 900,
        768: 500,
        "source_default": 900,
        "img_default": 500
    },
    "COMFRPTC34": {
        1562: 1800,
        1041: 1200,
        781: 900,
        768: 500,
        "source_default": 900,
        "img_default": 500
    },
    "COMFRPTC15": {
        768: 300,
        "source_default": 150,
        "img_default": 150
    },
    "COMFRPTC23": {
        1440: 360,
        "source_default": 120,
        "img_default": 120
    },
    "COMFRPTC17": {
        "source_default": 500,
        "img_default": 500
    },
    "COMFRPTC21": {
        1562: 900,
        768: 500,
        "source_default": 900,
        "img_default": 500
    },
    "GSTFRPTA15": {
        1562: 900,
        "source_default": 900,
        "img_default": 500
    },
    "COMFRPTC03": {
        768: 500,
        "source_default": 500,
        "img_default": 500
    },
    "COMFRPTC30": {
        768: 500,
        "source_default": 500,
        "img_default": 500
    },
    "THUMBNAIL": {
        "source_default": 500,
        "img_default": 500
    }
}


# 確認する拡張子
SUPPORTED_EXTENSIONS = ["webp", "WEBP", "jpg", "png", "JPG", "PNG" ]

# WebP保存設定
WEBP_QUALITY = 100
WEBP_METHOD = 6
WEBP_LOSSLESS = False

# ログ設定
LOG_DIR = ".logs"
LOG_FILE = "LOG.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"