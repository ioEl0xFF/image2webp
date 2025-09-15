"""
エラーハンドリングシステムのテスト
"""

import pytest
import logging
from unittest.mock import Mock, patch
from src.img2webp.utils.error_handler import (
    ErrorHandler, 
    error_handler, 
    ValidationError,
    validate_input,
    validate_file_path,
    validate_directory_path
)
from src.img2webp.utils.exceptions import Img2WebpError


class TestErrorHandler:
    """ErrorHandlerクラスのテスト"""
    
    def test_handle_error_with_reraise(self):
        """エラー再発生のテスト"""
        handler = ErrorHandler("test")
        
        with pytest.raises(ValueError):
            try:
                raise ValueError("test error")
            except ValueError as e:
                handler.handle_error(e, "test context", reraise=True)
    
    def test_handle_error_without_reraise(self, caplog):
        """エラー再発生なしのテスト"""
        handler = ErrorHandler("test")
        
        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("test error")
            except ValueError as e:
                handler.handle_error(e, "test context", reraise=False)
        
        assert "test context: test error" in caplog.text
    
    def test_safe_execute_success(self):
        """safe_execute成功時のテスト"""
        handler = ErrorHandler("test")
        
        def test_func(x, y):
            return x + y
        
        result = handler.safe_execute(test_func, 1, 2)
        assert result == 3
    
    def test_safe_execute_failure(self, caplog):
        """safe_execute失敗時のテスト"""
        handler = ErrorHandler("test")
        
        def test_func():
            raise ValueError("test error")
        
        with caplog.at_level(logging.ERROR):
            result = handler.safe_execute(
                test_func, 
                context="test context",
                default_return="default"
            )
        
        assert result == "default"
        assert "test context" in caplog.text


class TestErrorHandlerDecorator:
    """エラーハンドリングデコレータのテスト"""
    
    def test_error_handler_decorator_success(self):
        """デコレータ成功時のテスト"""
        @error_handler(context="test function")
        def test_func(x, y):
            return x + y
        
        result = test_func(1, 2)
        assert result == 3
    
    def test_error_handler_decorator_failure(self):
        """デコレータ失敗時のテスト"""
        @error_handler(context="test function", reraise=True, error_type=Img2WebpError)
        def test_func():
            raise ValueError("original error")
        
        with pytest.raises(Img2WebpError) as exc_info:
            test_func()
        
        assert "test function" in str(exc_info.value)


class TestValidation:
    """バリデーション関数のテスト"""
    
    def test_validate_input_success(self):
        """validate_input成功時のテスト"""
        # エラーが発生しないことを確認
        validate_input(5, lambda x: x > 0, "must be positive")
        validate_input("hello", lambda x: isinstance(x, str), "must be string")
    
    def test_validate_input_failure(self):
        """validate_input失敗時のテスト"""
        with pytest.raises(ValidationError) as exc_info:
            validate_input(-1, lambda x: x > 0, "must be positive")
        
        assert "must be positive" in str(exc_info.value)
    
    def test_validate_file_path_success(self, tmp_path):
        """validate_file_path成功時のテスト"""
        # テストファイルを作成
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # エラーが発生しないことを確認
        validate_file_path(str(test_file), must_exist=True)
        validate_file_path("/nonexistent/path", must_exist=False)
    
    def test_validate_file_path_failure(self):
        """validate_file_path失敗時のテスト"""
        with pytest.raises(ValidationError):
            validate_file_path("", must_exist=False)
        
        with pytest.raises(ValidationError):
            validate_file_path("/nonexistent/file.txt", must_exist=True)
    
    def test_validate_directory_path_success(self, tmp_path):
        """validate_directory_path成功時のテスト"""
        # エラーが発生しないことを確認
        validate_directory_path(str(tmp_path), must_exist=True)
        validate_directory_path("/nonexistent/dir", must_exist=False)
    
    def test_validate_directory_path_failure(self):
        """validate_directory_path失敗時のテスト"""
        with pytest.raises(ValidationError):
            validate_directory_path("", must_exist=False)
        
        with pytest.raises(ValidationError):
            validate_directory_path("/nonexistent/directory", must_exist=True)


if __name__ == "__main__":
    pytest.main([__file__])
