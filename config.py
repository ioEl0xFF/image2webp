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
# ＜画像＞ or ＜画像名＞ 両方対応、全角括弧補足も対応
# IMAGE_PATTERNの正規表現解説
#
# このパターンは、以下のような文字列から画像名を抽出します。
# 例: ＜画像＞sample-image-01
#     ＜画像名＞sample-image-02
#     ＜画像1＞sample-image-03
#     ＜画像（補足）＞sample-image-04
#     ＜画像名（説明）＞sample-image-05
#
# 正規表現の各部分の意味:
# ＜画像         ：全角の「＜画像」で始まる
# (?:名|\d*)?    ：「名」または数字（0個以上）が続く場合もOK（例: 画像名, 画像1, 画像12 など）
# (?:（[^）]*）)?：全角カッコ内の任意文字列（補足情報など）があればマッチ（例: 画像（補足））
# ＞             ：全角の「＞」で区切る
# \s*            ：「＞」の後に空白が0個以上あってもOK
# ([a-zA-Z0-9\-]+)：半角英数字・ハイフンからなる画像名部分をキャプチャ
#
# まとめると、「＜画像＞」や「＜画像名＞」、「＜画像1＞」、「＜画像（補足）＞」など多様な表記に対応し、
# その直後の画像名（英数字・ハイフン）を抽出します。
IMAGE_PATTERN = r"＜画像(?:名|\d*)?(?:（[^）]*）)?＞\s*([a-zA-Z0-9\-_]+)"

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
    "THUMBNAIL" : [[900, 600]],
}

# HTMLの画像置き換え順
HTML_IMAGE_REPLACE_ORDER = {
    "COMFRPTC09": [1800, 1200, 900, 500, 900, 900],
    "COMFRPTC12": [1200, 900, 500, 900, 500],
    "COMFRPTC14": [800, 600, 400, 400],
    "COMFRPTC13": [1200, 900, 500, 900, 500],
    "COMFRPTC34": [1800, 1200, 900, 500, 900],
    "COMFRPTC15": [300, 150, 150],
    "COMFRPTC23": [360, 240, 120, 120],
    "COMFRPTC17": [900, 500, 500],
    "COMFRPTC21": [900, 500, 900],
    "GSTFRPTA15": [900, 500, 900],
    "COMFRPTC03": [900, 500, 500],
    "COMFRPTC30": [900, 500, 500],
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