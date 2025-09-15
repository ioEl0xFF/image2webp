"""
カスタム例外クラス
アプリケーション固有の例外を定義
"""

class Img2WebpError(Exception):
    """img2webpアプリケーション共通の基底例外クラス"""
    pass


class DocxFileError(Img2WebpError):
    """DOCXファイル関連のエラー"""
    pass


class ImageFileError(Img2WebpError):
    """画像ファイル関連のエラー"""
    pass


class ImageConversionError(ImageFileError):
    """画像変換処理のエラー"""
    pass


class HtmlProcessingError(Img2WebpError):
    """HTML処理関連のエラー"""
    pass


class ConfigurationError(Img2WebpError):
    """設定関連のエラー"""
    pass
