"""
ファイル管理システムのテスト
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.img2webp.core.directory_manager import DirectoryManager
from src.img2webp.core.file_scanner import FileScanner
from src.img2webp.core.result_manager import ResultManager
from src.img2webp.core.file_manager import FileManager


class TestDirectoryManager:
    """DirectoryManagerクラスのテスト"""
    
    @patch('src.img2webp.core.directory_manager.config_loader')
    def test_create_output_directory(self, mock_config_loader, tmp_path):
        """出力ディレクトリ作成のテスト"""
        # モックの設定
        mock_directories = Mock()
        mock_directories.output_base_dir = str(tmp_path / "output")
        mock_config_loader.get_directories.return_value = mock_directories
        
        manager = DirectoryManager()
        
        # テストファイルパス
        test_docx = str(tmp_path / "test.docx")
        
        # ディレクトリ作成をテスト
        output_dir = manager.create_output_directory(test_docx)
        
        assert Path(output_dir).exists()
        assert Path(output_dir).name == "test"
    
    @patch('src.img2webp.core.directory_manager.config_loader')
    def test_ensure_base_directories(self, mock_config_loader, tmp_path):
        """基本ディレクトリ作成のテスト"""
        # モックの設定
        mock_directories = Mock()
        mock_directories.output_base_dir = str(tmp_path / "output")
        mock_directories.log_dir = str(tmp_path / "logs")
        mock_config_loader.get_directories.return_value = mock_directories
        
        manager = DirectoryManager()
        manager.ensure_base_directories()
        
        assert (tmp_path / "output").exists()
        assert (tmp_path / "logs").exists()


class TestFileScanner:
    """FileScannerクラスのテスト"""
    
    @patch('src.img2webp.core.file_scanner.config_loader')
    def test_get_docx_files(self, mock_config_loader, tmp_path):
        """DOCXファイル取得のテスト"""
        # テストディレクトリとファイルを作成
        docx_dir = tmp_path / "docx"
        docx_dir.mkdir()
        
        # テストファイルを作成
        (docx_dir / "test1.docx").touch()
        (docx_dir / "test2.docx").touch()
        (docx_dir / "~$temp.docx").touch()  # 一時ファイル
        (docx_dir / "other.txt").touch()     # 非DOCXファイル
        
        # モックの設定
        mock_directories = Mock()
        mock_directories.docx_directory = str(docx_dir)
        mock_config_loader.get_directories.return_value = mock_directories
        
        scanner = FileScanner()
        docx_files = scanner.get_docx_files()
        
        # 結果の検証
        assert len(docx_files) == 2
        file_names = [Path(f).name for f in docx_files]
        assert "test1.docx" in file_names
        assert "test2.docx" in file_names
        assert "~$temp.docx" not in file_names  # 一時ファイルは除外
    
    @patch('src.img2webp.core.file_scanner.config_loader')
    def test_find_html_file(self, mock_config_loader, tmp_path):
        """HTMLファイル検索のテスト"""
        # テストディレクトリとファイルを作成
        html_dir = tmp_path / "html"
        html_dir.mkdir()
        (html_dir / "test.html").touch()
        
        # モックの設定
        mock_directories = Mock()
        mock_directories.html_dir = str(html_dir)
        mock_config_loader.get_directories.return_value = mock_directories
        
        scanner = FileScanner()
        
        # 存在するファイル
        docx_file = str(tmp_path / "test.docx")
        html_file = scanner.find_html_file(docx_file)
        assert html_file == str(html_dir / "test.html")
        
        # 存在しないファイル
        docx_file = str(tmp_path / "nonexistent.docx")
        html_file = scanner.find_html_file(docx_file)
        assert html_file is None


class TestResultManager:
    """ResultManagerクラスのテスト"""
    
    @patch('src.img2webp.core.result_manager.config_loader')
    def test_save_results(self, mock_config_loader, tmp_path):
        """結果保存のテスト"""
        # モックの設定
        mock_directories = Mock()
        mock_directories.log_dir = str(tmp_path / "logs")
        mock_config_loader.get_directories.return_value = mock_directories
        
        manager = ResultManager()
        
        # テストデータ
        image_names = [
            {"image_name": "test1", "file": "doc1.docx"},
            {"image_name": "test2", "file": "doc2.docx"}
        ]
        converted_images = [
            "/output/test1_400.webp",
            "/output/test2_800.webp"
        ]
        
        # 結果保存
        manager.save_results(image_names, converted_images)
        
        # ファイルが作成されているか確認
        log_dir = tmp_path / "logs"
        assert (log_dir / "all_image_names.json").exists()
        assert (log_dir / "all_converted_images.txt").exists()
        
        # ファイル内容の確認
        import json
        with open(log_dir / "all_image_names.json", "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data == image_names
        
        with open(log_dir / "all_converted_images.txt", "r", encoding="utf-8") as f:
            saved_images = f.read().strip().split("\n")
        assert saved_images == converted_images


class TestFileManager:
    """FileManager統合クラスのテスト"""
    
    def test_file_manager_integration(self):
        """FileManager統合テスト"""
        manager = FileManager()
        
        # 各コンポーネントが正しく初期化されているか確認
        assert hasattr(manager, '_directory_manager')
        assert hasattr(manager, '_file_scanner')
        assert hasattr(manager, '_result_manager')
        
        # メソッドが委譲されているか確認
        assert hasattr(manager, 'get_docx_files')
        assert hasattr(manager, 'validate_docx_files')
        assert hasattr(manager, 'create_output_directory')
        assert hasattr(manager, 'find_html_file')
        assert hasattr(manager, 'save_results')


if __name__ == "__main__":
    pytest.main([__file__])
