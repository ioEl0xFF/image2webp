"""
img2webp.core - コア機能モジュール

DOCXファイル解析、画像処理、HTML処理、ファイル管理などの
コア機能を提供します。
"""

from .docx_parser import DocxAnalyzer
from .image_processor import ImageProcessor
from .html_processor import HtmlProcessor
from .file_manager import FileManager

__all__ = [
    "DocxAnalyzer",
    "ImageProcessor", 
    "HtmlProcessor",
    "FileManager"
]
