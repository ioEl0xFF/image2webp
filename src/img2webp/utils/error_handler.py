"""
エラーハンドリングユーティリティ
統一されたエラーハンドリング機能を提供
"""

import logging
import traceback
from typing import Any, Callable, Optional, Type, Union
from functools import wraps

from .exceptions import Img2WebpError


class ErrorHandler:
    """統一されたエラーハンドリングを提供するクラス"""
    
    def __init__(self, logger_name: str = __name__):
        self._logger = logging.getLogger(logger_name)
    
    def handle_error(self, 
                    error: Exception, 
                    context: str = "", 
                    reraise: bool = True,
                    error_type: Optional[Type[Exception]] = None) -> None:
        """
        エラーを統一的に処理
        
        Args:
            error: 発生したエラー
            context: エラーが発生したコンテキスト
            reraise: エラーを再発生させるか
            error_type: 再発生させるエラーの型
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        
        # ログレベルを決定
        if isinstance(error, Img2WebpError):
            self._logger.error(error_msg)
        else:
            self._logger.error(f"予期しないエラー - {error_msg}")
            self._logger.debug(traceback.format_exc())
        
        if reraise:
            if error_type:
                raise error_type(error_msg) from error
            else:
                raise
    
    def safe_execute(self, 
                    func: Callable[..., Any], 
                    *args, 
                    context: str = "",
                    default_return: Any = None,
                    error_types: tuple = (Exception,),
                    **kwargs) -> Any:
        """
        関数を安全に実行し、エラーをハンドリング
        
        Args:
            func: 実行する関数
            *args: 関数の位置引数
            context: エラーコンテキスト
            default_return: エラー時のデフォルト戻り値
            error_types: キャッチするエラーの型
            **kwargs: 関数のキーワード引数
            
        Returns:
            関数の戻り値またはデフォルト戻り値
        """
        try:
            return func(*args, **kwargs)
        except error_types as e:
            self.handle_error(e, context, reraise=False)
            return default_return


def error_handler(context: str = "", 
                 reraise: bool = True,
                 error_type: Optional[Type[Exception]] = None,
                 logger_name: Optional[str] = None):
    """
    エラーハンドリングデコレータ
    
    Args:
        context: エラーコンテキスト
        reraise: エラーを再発生させるか
        error_type: 再発生させるエラーの型
        logger_name: ロガー名
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            handler = ErrorHandler(logger_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = context or f"{func.__name__}の実行中"
                handler.handle_error(e, error_context, reraise, error_type)
        
        return wrapper
    return decorator


def safe_file_operation(operation: str = "ファイル操作"):
    """
    ファイル操作用のエラーハンドリングデコレータ
    
    Args:
        operation: 操作の説明
    """
    return error_handler(
        context=operation,
        reraise=True,
        error_type=Img2WebpError
    )


def safe_conversion_operation(operation: str = "変換処理"):
    """
    変換処理用のエラーハンドリングデコレータ
    
    Args:
        operation: 操作の説明
    """
    return error_handler(
        context=operation,
        reraise=False  # 変換エラーは処理を継続
    )


class ValidationError(Img2WebpError):
    """バリデーションエラー"""
    pass


def validate_input(value: Any, 
                  validator: Callable[[Any], bool], 
                  error_message: str) -> None:
    """
    入力値をバリデーション
    
    Args:
        value: バリデーションする値
        validator: バリデーション関数
        error_message: エラーメッセージ
        
    Raises:
        ValidationError: バリデーションに失敗した場合
    """
    if not validator(value):
        raise ValidationError(error_message)


def validate_file_path(file_path: str, must_exist: bool = True) -> None:
    """
    ファイルパスをバリデーション
    
    Args:
        file_path: ファイルパス
        must_exist: ファイルが存在する必要があるか
        
    Raises:
        ValidationError: バリデーションに失敗した場合
    """
    if not file_path:
        raise ValidationError("ファイルパスが指定されていません")
    
    from pathlib import Path
    path = Path(file_path)
    
    if must_exist and not path.exists():
        raise ValidationError(f"ファイルが存在しません: {file_path}")
    
    if must_exist and not path.is_file():
        raise ValidationError(f"指定されたパスはファイルではありません: {file_path}")


def validate_directory_path(dir_path: str, must_exist: bool = True) -> None:
    """
    ディレクトリパスをバリデーション
    
    Args:
        dir_path: ディレクトリパス
        must_exist: ディレクトリが存在する必要があるか
        
    Raises:
        ValidationError: バリデーションに失敗した場合
    """
    if not dir_path:
        raise ValidationError("ディレクトリパスが指定されていません")
    
    from pathlib import Path
    path = Path(dir_path)
    
    if must_exist and not path.exists():
        raise ValidationError(f"ディレクトリが存在しません: {dir_path}")
    
    if must_exist and not path.is_dir():
        raise ValidationError(f"指定されたパスはディレクトリではありません: {dir_path}")
