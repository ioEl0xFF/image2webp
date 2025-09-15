"""
img2webp.utils - ユーティリティモジュール

ログ機能、例外クラス、画像処理ユーティリティを提供します。
"""

from .logger import setup_logging, get_missing_images_count
from .exceptions import (
    Img2WebpError, DocxFileError, ImageFileError,
    ImageConversionError, HtmlProcessingError, ConfigurationError
)
from .image_utils import (
    has_alpha, load_image_with_exif, resize_fit, 
    ensure_rgba_or_rgb, save_webp, is_webp_image,
    convert_image_with_pillow, find_input_image
)

__all__ = [
    "setup_logging",
    "get_missing_images_count",
    "Img2WebpError", 
    "DocxFileError", 
    "ImageFileError",
    "ImageConversionError", 
    "HtmlProcessingError", 
    "ConfigurationError",
    "has_alpha", 
    "load_image_with_exif", 
    "resize_fit",
    "ensure_rgba_or_rgb", 
    "save_webp",
    "is_webp_image",
    "convert_image_with_pillow",
    "find_input_image"
]
