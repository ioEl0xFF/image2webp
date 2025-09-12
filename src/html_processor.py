"""
HTML処理モジュール
HTMLファイル内の画像名置換とメディアクエリ解析を担当
"""

import re
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

from . import config
from .exceptions import HtmlProcessingError
from .logger_utils import get_logger


class HtmlProcessor:
    """HTML画像名置換処理を担当するクラス"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def process_html_file(self, html_file_path: str, image_names: List[Dict[str, str]]) -> bool:
        """
        HTMLファイルの画像名置換処理を実行
        
        Args:
            html_file_path: HTMLファイルのパス
            image_names: 画像名情報のリスト
            
        Returns:
            処理成功時True、失敗時False
        """
        try:
            html_content = self._read_html_file(html_file_path)
            if not html_content:
                return False
            
            self.logger.info(f"HTML画像名置換処理開始: {html_file_path}")
            print("=== HTML画像名置換処理実行 ===")
            
            # 各画像名ごとに処理
            for record in image_names:
                row_index = record["row_index"]
                image_name = record["image_name"]
                
                print(f"処理対象: row_index={row_index}, image_name={image_name}")
                
                # コード部分を抽出
                code = self._extract_code_from_row_index(row_index)
                if not code:
                    continue
                
                # メディアクエリ置換が可能な場合は実行
                if code in config.MIN_WIDTH_SIZE_MAP:
                    print(f"  {code}のメディアクエリベース置換を実行")
                    html_content = self._replace_image_names_by_media_query(
                        html_content, image_name, code
                    )
                else:
                    print(f"  {code}のメディアクエリベース置換を実行できません。スキップ: {image_name}")
                    self.logger.warning(f"メディアクエリベース置換できません: {code} - スキップ: {image_name}")
                    continue
            
            # 置換後のHTMLファイルを保存
            self._save_html_file(html_file_path, html_content)
            return True
            
        except Exception as e:
            self.logger.error(f"HTML処理エラー: {html_file_path} - {e}")
            return False
    
    def _read_html_file(self, html_file_path: str) -> Optional[str]:
        """
        HTMLファイルを読み込む
        
        Args:
            html_file_path: HTMLファイルのパス
            
        Returns:
            HTMLファイルの内容、失敗時はNone
        """
        try:
            with open(html_file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[ERROR] HTMLファイルの読み込みに失敗しました: {html_file_path} ({e})")
            self.logger.error(f"HTMLファイルの読み込み失敗: {html_file_path} ({e})")
            return None
    
    def _save_html_file(self, html_file_path: str, html_content: str) -> None:
        """
        HTMLファイルを保存
        
        Args:
            html_file_path: HTMLファイルのパス
            html_content: HTMLファイルの内容
        """
        try:
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"HTMLファイル更新完了: {html_file_path}")
            self.logger.info(f"HTMLファイル更新完了: {html_file_path}")
        except Exception as e:
            print(f"[ERROR] HTMLファイルの保存に失敗しました: {html_file_path} ({e})")
            self.logger.error(f"HTMLファイル保存失敗: {html_file_path} ({e})")
            raise HtmlProcessingError(f"HTMLファイル保存失敗: {html_file_path}") from e
    
    def _extract_code_from_row_index(self, row_index: str) -> Optional[str]:
        """
        row_indexからコード部分を抽出
        
        Args:
            row_index: 行インデックス（左セルのテキスト）
            
        Returns:
            抽出されたコード、失敗時はNone
        """
        code_match = re.match(config.CODE_PATTERN, row_index)
        if not code_match:
            print(f"  [WARN] コード抽出失敗: {row_index}")
            self.logger.warning(f"コード抽出失敗: {row_index}")
            return None
        
        return code_match.group(1)
    
    def _replace_image_names_by_media_query(self, html_content: str, image_name: str, code: str) -> str:
        """
        メディアクエリに基づいてHTMLファイル内の画像名を置き換える
        
        Args:
            html_content: HTMLファイルの内容
            image_name: 画像名
            code: コード（COMFRPTC12など）
            
        Returns:
            置き換え後のHTMLコンテンツ
        """
        # <source>タグの処理
        html_content = self._replace_source_tags(html_content, image_name, code)
        
        # <img>タグの処理
        html_content = self._replace_img_tags(html_content, image_name, code)
        
        return html_content
    
    def _replace_source_tags(self, html_content: str, image_name: str, code: str) -> str:
        """
        <source>タグの画像名を置き換える
        
        Args:
            html_content: HTMLファイルの内容
            image_name: 画像名
            code: コード
            
        Returns:
            置き換え後のHTMLコンテンツ
        """
        source_pattern = rf'<source[^>]*data-srcset="[^"]*{re.escape(image_name)}[^"]*"[^>]*>'
        
        def replace_source_tag(match):
            source_tag = match.group(0)
            tag_position = match.start()
            
            # HTMLコンテキストを取得
            html_context = self._get_html_context_for_image(html_content, image_name, tag_position)
            
            # メディアクエリを抽出
            media_match = re.search(r'media="([^"]*)"', source_tag)
            if not media_match:
                print(f"    [INFO] メディアクエリが見つかりません。source_defaultを適用: {source_tag[:100]}...")
                media_query = ""
            else:
                media_query = media_match.group(1)
            
            # 適切な画像サイズを取得
            size = self._get_image_size_from_media_query(
                media_query, code, "source", html_context, html_content, tag_position
            )
            if not size:
                print(f"    [WARN] サイズが決定できません: {media_query}")
                return source_tag
            
            # 画像ファイル名を置換
            new_filename = f"{image_name}{size}.webp"
            new_source_tag = re.sub(
                rf'{re.escape(image_name)}[^"]*\.(jpg|jpeg|png|webp|JPG|JPEG|PNG|WEBP)',
                new_filename,
                source_tag,
                flags=re.IGNORECASE
            )
            
            # ログ出力用の理由情報を生成
            reason_info = self._generate_reason_info(code, media_query, html_content, tag_position)
            
            print(f"    メディアクエリ置換: {media_query} → {new_filename}{reason_info}")
            self.logger.info(f"メディアクエリ置換: {media_query} → {new_filename}{reason_info}")
            
            return new_source_tag
        
        return re.sub(source_pattern, replace_source_tag, html_content, flags=re.IGNORECASE)
    
    def _replace_img_tags(self, html_content: str, image_name: str, code: str) -> str:
        """
        <img>タグの画像名を置き換える
        
        Args:
            html_content: HTMLファイルの内容
            image_name: 画像名
            code: コード
            
        Returns:
            置き換え後のHTMLコンテンツ
        """
        img_pattern = rf'<img[^>]*data-src="[^"]*{re.escape(image_name)}[^"]*"[^>]*>'
        
        def replace_img_tag(match):
            img_tag = match.group(0)
            tag_position = match.start()
            
            # HTMLコンテキストを取得
            html_context = self._get_html_context_for_image(html_content, image_name, tag_position)
            
            # imgタグ用のデフォルトサイズを取得
            default_size = self._get_image_size_from_media_query("", code, "img", html_context)
            new_filename = f"{image_name}{default_size}.webp"
            
            new_img_tag = re.sub(
                rf'{re.escape(image_name)}[^"]*\.(jpg|jpeg|png|webp|JPG|JPEG|PNG|WEBP)',
                new_filename,
                img_tag,
                flags=re.IGNORECASE
            )
            
            print(f"    IMGタグ置換: → {new_filename}")
            self.logger.info(f"IMGタグ置換: → {new_filename}")
            
            return new_img_tag
        
        return re.sub(img_pattern, replace_img_tag, html_content, flags=re.IGNORECASE)
    
    def _get_html_context_for_image(self, html_content: str, image_name: str, tag_position: int) -> str:
        """
        画像タグの周辺のHTMLコンテキスト（クラス名など）を取得
        
        Args:
            html_content: HTMLファイルの内容
            image_name: 画像名
            tag_position: タグの位置
            
        Returns:
            HTMLコンテキスト文字列
        """
        # タグの前後200文字を取得してコンテキストを分析
        start = max(0, tag_position - 200)
        end = min(len(html_content), tag_position + 200)
        return html_content[start:end]
    
    def _is_carousel_for_comfrptc12(self, html_content: str, tag_position: int) -> bool:
        """
        COMFRPTC12専用のカーセル判定を行う
        
        Args:
            html_content: HTMLファイルの内容
            tag_position: タグの位置
            
        Returns:
            True: カーセル版, False: 通常版
        """
        # ファイル名が見つかった行から上に順番に探索
        lines = html_content[:tag_position].split('\n')
        
        # 後ろから50行まで探索
        search_lines = lines[-50:] if len(lines) >= 50 else lines
        
        for line in reversed(search_lines):
            # "_carousel"が見つかった場合はカーセル版
            if "_carousel" in line:
                return True
            # "mCommonsectionImgitem"が見つかった場合は通常版
            if "mCommonsectionImgitem" in line:
                return False
        
        # 50行探しても見つからない場合は通常版
        return False
    
    def _get_image_size_from_media_query(
        self, 
        media_query: str, 
        code: str, 
        tag_type: str = "source", 
        html_context: str = "", 
        html_content: str = "", 
        tag_position: int = 0
    ) -> Optional[int]:
        """
        メディアクエリから適切な画像サイズを取得する
        
        Args:
            media_query: メディアクエリ文字列
            code: コード（COMFRPTC12など）
            tag_type: タグの種類（"source" または "img"）
            html_context: HTMLコンテキスト（クラス名など）
            html_content: HTMLファイルの内容（COMFRPTC12のカーセル判定用）
            tag_position: タグの位置（COMFRPTC12のカーセル判定用）
            
        Returns:
            画像サイズ（ピクセル）、決定できない場合はNone
        """
        if code not in config.MIN_WIDTH_SIZE_MAP:
            return None
        
        size_map = config.MIN_WIDTH_SIZE_MAP[code]
        
        # メディアクエリからmin-widthの値を抽出
        width_match = re.search(r'\(min-width:\s*(\d+)px\)', media_query)
        if not width_match:
            # メディアクエリがない場合はデフォルトサイズを返す
            default_key = f"{tag_type}_default"
            return size_map.get(default_key, 500)
        
        width = int(width_match.group(1))
        
        # 解像度条件をチェック
        has_2dppx = 'min-resolution:2dppx' in media_query
        
        # 複数サイズ対応の場合は、解像度条件とクラス名に応じて選択
        if width in size_map:
            size_value = size_map[width]
            
            if isinstance(size_value, list):
                # 複数サイズがある場合
                if has_2dppx:
                    # 高解像度の場合
                    if code == "COMFRPTC12" and (width == 1562 or width == 1041):
                        # COMFRPTC12の1562pxまたは1041pxの特別処理
                        if html_content and tag_position > 0:
                            # 新しいカーセル判定ロジックを使用
                            is_carousel = self._is_carousel_for_comfrptc12(html_content, tag_position)
                        else:
                            # フォールバック: 従来の方法
                            is_carousel = "_carousel" in html_context
                        
                        if is_carousel:
                            # カルーセルの場合は大きいサイズ（1800または1200）
                            return max(size_value)
                        else:
                            # 通常表示の場合は小さいサイズ（900）
                            return min(size_value)
                    else:
                        # その他の場合は大きいサイズを選択
                        return max(size_value)
                else:
                    # 通常解像度の場合は小さいサイズを選択
                    return min(size_value)
            else:
                # 単一サイズの場合
                return size_value
        
        # COMFRPTC23の特別処理：min-widthがない場合の判別
        if code == "COMFRPTC23" and not width_match:
            if has_2dppx:
                # (min-resolution: 2dppx) のみの場合 → 240
                return 240
            else:
                # 条件なしの場合 → 120
                return 120
        
        # 該当するmin-widthがない場合はデフォルトサイズを返す
        default_key = f"{tag_type}_default"
        return size_map.get(default_key, 500)
    
    def _generate_reason_info(self, code: str, media_query: str, html_content: str, tag_position: int) -> str:
        """
        COMFRPTC12とCOMFRPTC23の特別な判別理由を生成
        
        Args:
            code: コード
            media_query: メディアクエリ
            html_content: HTMLファイルの内容
            tag_position: タグの位置
            
        Returns:
            理由情報文字列
        """
        reason_info = ""
        
        if code == "COMFRPTC12":
            # メディアクエリからmin-widthの値を再抽出
            width_match = re.search(r'\(min-width:\s*(\d+)px\)', media_query)
            has_2dppx = 'min-resolution:2dppx' in media_query
            
            if width_match and has_2dppx:
                width = int(width_match.group(1))
                is_carousel = self._is_carousel_for_comfrptc12(html_content, tag_position)
                if width == 1562:
                    if is_carousel:
                        reason_info = " (カルーセル1800)"
                    else:
                        reason_info = " (通常表示900)"
                elif width == 1041:
                    if is_carousel:
                        reason_info = " (カルーセル1200)"
                    else:
                        reason_info = " (通常表示900)"
        elif code == "COMFRPTC23":
            # メディアクエリからmin-widthの値を再抽出
            width_match = re.search(r'\(min-width:\s*(\d+)px\)', media_query)
            has_2dppx = 'min-resolution:2dppx' in media_query
            
            if not width_match:
                if has_2dppx:
                    reason_info = " (解像度のみ240)"
                else:
                    reason_info = " (条件なし120)"
            elif width_match and int(width_match.group(1)) == 1440 and has_2dppx:
                reason_info = " (1440px+2dppx360)"
        
        return reason_info
