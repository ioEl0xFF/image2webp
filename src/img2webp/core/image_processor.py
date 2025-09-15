"""
画像処理モジュール
画像変換処理を担当
"""

import os
from typing import List, Dict, Tuple, Optional
import logging

from ..config.loader import config_loader
from ..utils import image_utils
from ..utils.exceptions import ImageFileError, ImageConversionError
from ..utils.logger import record_missing_image
from ..utils.error_handler import (
    ErrorHandler, 
    safe_conversion_operation, 
    validate_input,
    ValidationError
)


class ImageProcessor:
    """画像変換処理を担当するクラス"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler(__name__)
        self._config = config_loader.config
        self._patterns_config = config_loader.get_patterns()
    
    def process_images(self, image_names: List[Dict[str, str]], file_info: Dict[str, str]) -> List[str]:
        """
        画像変換処理を実行
        
        Args:
            image_names: 画像名情報のリスト
            file_info: ファイル情報
            
        Returns:
            変換された画像ファイルのパスのリスト
        """
        try:
            validate_input(image_names, lambda x: isinstance(x, list), "画像名情報は配列である必要があります")
            validate_input(file_info, lambda x: isinstance(x, dict) and 'file_name' in x, 
                          "ファイル情報が不正です")
            
            print("=== 画像変換処理開始 ===")
            self._logger.info(f"画像変換処理開始: {file_info['file_name']}")
            
            converted_images = []
            
            for record in image_names:
                converted_files = self._error_handler.safe_execute(
                    self._process_single_image,
                    record, file_info,
                    context=f"画像処理: {record.get('image_name', '不明')}",
                    default_return=[]
                )
                if converted_files:
                    converted_images.extend(converted_files)
            
            print(f"=== ファイル {file_info['file_name']} 処理完了 ===")
            self._logger.info(f"ファイル処理完了: {file_info['file_name']} - 変換画像数: {len(converted_images)}")
            
            return converted_images
            
        except ValidationError as e:
            self._error_handler.handle_error(e, "画像処理の入力検証")
            return []
    
    def _process_single_image(self, record: Dict[str, str], file_info: Dict[str, str]) -> List[str]:
        """
        単一の画像を処理
        
        Args:
            record: 画像名情報
            file_info: ファイル情報
            
        Returns:
            変換された画像ファイルのパスのリスト
        """
        row_text = record["row_index"]
        image_name = record["image_name"]
        output_dir = record["output_dir"]
        
        print(f"処理対象: row_index={row_text}, image_name={image_name}")
        
        # コード抽出
        code = self._extract_code_from_row_index(row_text)
        if not code:
            return []
        
        if code not in self._config.width_map:
            print(f"  [WARN] {code} の幅未定義。スキップ: {image_name}")
            self._logger.warning(f"幅未定義: {code} - スキップ: {image_name}")
            return []
        
        sizes = self._config.width_map[code]
        
        # 入力ファイル確認
        input_file = image_utils.find_input_image(image_name)
        if not input_file:
            print(f"  [ERROR] 入力ファイルが存在しません: {image_name} (jpg/png/webp)")
            self._logger.error(f"入力ファイルが存在しません: {image_name}")
            # 存在しない画像名をファイルに記録
            record_missing_image(image_name, file_info['file_name_without_ext'], self._logger)
            return []
        
        print(f"  入力ファイル発見: {input_file}")
        
        # 幅ごとにWebP変換
        converted_files = []
        for size in sizes:
            converted_file = self._convert_single_size(
                input_file, image_name, size, output_dir
            )
            if converted_file:
                converted_files.append(converted_file)
        
        return converted_files
    
    def _convert_single_size(
        self, 
        input_file: str, 
        image_name: str, 
        size: List[int], 
        output_dir: str
    ) -> Optional[str]:
        """
        単一サイズでの画像変換
        
        Args:
            input_file: 入力ファイルのパス
            image_name: 画像名
            size: [幅, 高さ]のリスト
            output_dir: 出力ディレクトリ
            
        Returns:
            変換されたファイルのパス、失敗時はNone
        """
        output_file = f"{output_dir}/{image_name}{size[0]}.webp"
        
        # 出力ファイルが既に存在する場合はスキップ
        if os.path.exists(output_file):
            print(f"  → 出力ファイルが既に存在するため、{image_name} を {size}px 幅で WebP に変換しません")
            self._logger.info(f"スキップ: {image_name} - {size}px - 出力ファイルが既に存在")
            return output_file
        
        print(f"  → 変換開始: {input_file} → {output_file} (width={size[0]} height={size[1]})")
        
        # Pillowを使用して変換（WebP形式の場合はリサイズのみ）
        success = image_utils.convert_image_with_pillow(input_file, size, output_file)
        
        if success:
            print(f"    [OK] {image_name} を {size}px 幅で WebP に変換成功")
            self._logger.info(f"変換成功: {image_name} - {size}px")
            return output_file
        else:
            print(f"    [NG] {image_name} の変換失敗 ({size}px)")
            self._logger.error(f"変換失敗: {image_name} - {size}px")
            raise ImageConversionError(f"画像変換失敗: {image_name} - {size}px")
    
    def _extract_code_from_row_index(self, row_index: str) -> Optional[str]:
        """
        row_indexからコード部分を抽出
        
        Args:
            row_index: 行インデックス（左セルのテキスト）
            
        Returns:
            抽出されたコード、失敗時はNone
        """
        import re
        
        code_match = re.match(self._patterns_config.code_pattern, row_index)
        if not code_match:
            print(f"  [WARN] コード抽出失敗: {row_index}")
            self._logger.warning(f"コード抽出失敗: {row_index}")
            return None
        
        return code_match.group(1)
