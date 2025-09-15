"""
設定管理システムのテスト
"""

import pytest
import json
from pathlib import Path
from src.img2webp.config.loader import ConfigLoader, DirectoryConfig, AppConfig


class TestConfigLoader:
    """ConfigLoaderクラスのテスト"""
    
    def test_default_config_creation(self, tmp_path):
        """デフォルト設定の作成をテスト"""
        config_file = tmp_path / "test_config.json"
        loader = ConfigLoader(str(config_file))
        
        # デフォルト値の確認
        assert loader.get("directories.docx_directory") == "data/input/docx"
        assert loader.get("directories.output_base_dir") == "data/output"
        assert loader.get("image_processing.webp_quality") == 100
        
    def test_config_get_set(self, tmp_path):
        """設定の取得・設定をテスト"""
        config_file = tmp_path / "test_config.json"
        loader = ConfigLoader(str(config_file))
        
        # 設定値の設定
        loader.set("directories.docx_directory", "/custom/path")
        loader.set("image_processing.webp_quality", 80)
        
        # 設定値の確認
        assert loader.get("directories.docx_directory") == "/custom/path"
        assert loader.get("image_processing.webp_quality") == 80
        
    def test_config_persistence(self, tmp_path):
        """設定の永続化をテスト"""
        config_file = tmp_path / "test_config.json"
        
        # 最初のローダーで設定
        loader1 = ConfigLoader(str(config_file))
        loader1.set("directories.docx_directory", "/persistent/path")
        
        # 新しいローダーで設定が保持されているか確認
        loader2 = ConfigLoader(str(config_file))
        assert loader2.get("directories.docx_directory") == "/persistent/path"
        
    def test_typed_config_access(self, tmp_path):
        """型安全な設定アクセスをテスト"""
        config_file = tmp_path / "test_config.json"
        loader = ConfigLoader(str(config_file))
        
        # 型安全なアクセサの確認
        directories = loader.get_directories()
        assert isinstance(directories, DirectoryConfig)
        assert directories.docx_directory == "data/input/docx"
        
        image_processing = loader.get_image_processing()
        assert image_processing.webp_quality == 100
        assert image_processing.webp_lossless is True


class TestDirectoryConfig:
    """DirectoryConfigクラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値をテスト"""
        config = DirectoryConfig()
        assert config.docx_directory == "data/input/docx"
        assert config.output_base_dir == "data/output"
        assert config.images_dir == "data/input/images"
        assert config.html_dir == "data/input/html"
        assert config.log_dir == ".logs"
        
    def test_custom_values(self):
        """カスタム値をテスト"""
        config = DirectoryConfig(
            docx_directory="/custom/docx",
            output_base_dir="/custom/output"
        )
        assert config.docx_directory == "/custom/docx"
        assert config.output_base_dir == "/custom/output"
        # デフォルト値も確認
        assert config.images_dir == "data/input/images"


class TestAppConfig:
    """AppConfigクラスのテスト"""
    
    def test_create_default(self):
        """デフォルト設定作成をテスト"""
        config = AppConfig.create_default()
        
        assert isinstance(config.directories, DirectoryConfig)
        assert config.directories.docx_directory == "data/input/docx"
        assert config.image_processing.webp_quality == 100
        assert isinstance(config.width_map, dict)
        assert isinstance(config.min_width_size_map, dict)


if __name__ == "__main__":
    pytest.main([__file__])
