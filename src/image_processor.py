"""
画像処理モジュール
画像変換処理を担当
"""

import os
from typing import List, Dict, Tuple, Optional

from . import config
from . import image_utils
from .exceptions import ImageFileError, ImageConversionError
from .logger_utils import get_logger, record_missing_image


class ImageProcessor:
    """画像変換処理を担当するクラス"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def process_images(self, image_names: List[Dict[str, str]], file_info: Dict[str, str]) -> List[str]:
        """
        画像変換処理を実行
        
        Args:
            image_names: 画像名情報のリスト
            file_info: ファイル情報
            
        Returns:
            変換された画像ファイルのパスのリスト
        """
        print("=== 画像変換処理開始 ===")
        self.logger.info(f"画像変換処理開始: {file_info['file_name']}")
        
        converted_images = []
        
        for record in image_names:
            try:
                converted_files = self._process_single_image(record, file_info)
                converted_images.extend(converted_files)
            except Exception as e:
                self.logger.error(f"画像処理エラー: {record['image_name']} - {e}")
                continue
        
        print(f"=== ファイル {file_info['file_name']} 処理完了 ===")
        self.logger.info(f"ファイル処理完了: {file_info['file_name']} - 変換画像数: {len(converted_images)}")
        
        return converted_images
    
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
        
        if code not in config.WIDTH_MAP:
            print(f"  [WARN] {code} の幅未定義。スキップ: {image_name}")
            self.logger.warning(f"幅未定義: {code} - スキップ: {image_name}")
            return []
        
        sizes = config.WIDTH_MAP[code]
        
        # 入力ファイル確認
        input_file = image_utils.find_input_image(image_name)
        if not input_file:
            print(f"  [ERROR] 入力ファイルが存在しません: {image_name} (jpg/png/webp)")
            self.logger.error(f"入力ファイルが存在しません: {image_name}")
            # 存在しない画像名をファイルに記録
            record_missing_image(image_name, file_info['file_name_without_ext'], self.logger)
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
            self.logger.info(f"スキップ: {image_name} - {size}px - 出力ファイルが既に存在")
            return output_file
        
        print(f"  → 変換開始: {input_file} → {output_file} (width={size[0]} height={size[1]})")
        
        # Pillowを使用して変換（WebP形式の場合はリサイズのみ）
        success = image_utils.convert_image_with_pillow(input_file, size, output_file)
        
        if success:
            print(f"    [OK] {image_name} を {size}px 幅で WebP に変換成功")
            self.logger.info(f"変換成功: {image_name} - {size}px")
            return output_file
        else:
            print(f"    [NG] {image_name} の変換失敗 ({size}px)")
            self.logger.error(f"変換失敗: {image_name} - {size}px")
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
        
        code_match = re.match(config.CODE_PATTERN, row_index)
        if not code_match:
            print(f"  [WARN] コード抽出失敗: {row_index}")
            self.logger.warning(f"コード抽出失敗: {row_index}")
            return None
        
        return code_match.group(1)
