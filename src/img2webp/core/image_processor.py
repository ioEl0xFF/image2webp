"""
画像処理モジュール
画像変換処理を担当
"""

import os
from typing import List, Dict, Tuple, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import multiprocessing

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
        self._is_cancelled = False
        self._cancel_callback = None

        # マルチスレッド設定
        image_processing_config = config_loader.get_image_processing()
        configured_workers = image_processing_config.max_workers
        cpu_count = multiprocessing.cpu_count()

        # CPUコア数に基づいた最適化（最大でCPUコア数まで）
        self._max_workers = min(configured_workers, cpu_count)
        self._enable_multithreading = image_processing_config.enable_multithreading
        self._thread_lock = threading.Lock()
        self._progress_counter = 0
        self._total_images = 0

        self._logger.debug(f"マルチスレッド設定 - CPU数: {cpu_count}, 設定値: {configured_workers}, "
                          f"実際のワーカー数: {self._max_workers}, 有効: {self._enable_multithreading}")

    def set_cancel_callback(self, callback):
        """中断時のコールバック関数を設定"""
        self._cancel_callback = callback

    def cancel_processing(self):
        """処理を中断（マルチスレッド対応）"""
        with self._thread_lock:
            self._is_cancelled = True
        if self._cancel_callback:
            self._cancel_callback("画像処理が中断されました")
        self._logger.info("画像処理の中断が要求されました")

    def _check_cancellation(self) -> bool:
        """中断チェック（スレッドセーフ）"""
        with self._thread_lock:
            cancelled = self._is_cancelled

        if cancelled:
            if self._cancel_callback:
                self._cancel_callback("処理中断が検出されました")
            return True
        return False

    def process_images(self, image_names: List[Dict[str, str]], file_info: Dict[str, str]) -> List[str]:
        """
        画像変換処理を実行（マルチスレッド対応）

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

            self._logger.info(f"画像変換処理開始: {file_info['file_name']} - 対象画像数: {len(image_names)}")

            # プログレス管理の初期化
            self._progress_counter = 0
            self._total_images = len(image_names)

            # マルチスレッドが有効かつ複数の画像がある場合は並列処理
            if self._enable_multithreading and len(image_names) > 1:
                return self._process_images_multithreaded(image_names, file_info)
            else:
                return self._process_images_sequential(image_names, file_info)

        except ValidationError as e:
            self._error_handler.handle_error(e, "画像処理の入力検証")
            return []

    def _process_images_sequential(self, image_names: List[Dict[str, str]], file_info: Dict[str, str]) -> List[str]:
        """
        シーケンシャル（従来の）画像変換処理

        Args:
            image_names: 画像名情報のリスト
            file_info: ファイル情報

        Returns:
            変換された画像ファイルのパスのリスト
        """
        converted_images = []

        for i, record in enumerate(image_names):
            # 中断チェック
            if self._check_cancellation():
                self._logger.info(f"画像変換処理中断: {file_info['file_name']} - {i}/{len(image_names)}")
                break

            converted_files = self._error_handler.safe_execute(
                self._process_single_image,
                record, file_info,
                context=f"画像処理: {record.get('image_name', '不明')}",
                default_return=[]
            )
            if converted_files:
                converted_images.extend(converted_files)

        if not self._is_cancelled:
            self._logger.info(f"ファイル処理完了: {file_info['file_name']} - 変換画像数: {len(converted_images)}")

        return converted_images

    def _process_images_multithreaded(self, image_names: List[Dict[str, str]], file_info: Dict[str, str]) -> List[str]:
        """
        マルチスレッド画像変換処理

        Args:
            image_names: 画像名情報のリスト
            file_info: ファイル情報

        Returns:
            変換された画像ファイルのパスのリスト
        """
        self._logger.info(f"マルチスレッド処理開始 - ワーカー数: {self._max_workers}")

        converted_images = []
        start_time = time.time()

        try:
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                # 全画像処理タスクをサブミット
                future_to_record = {
                    executor.submit(self._process_single_image_thread_safe, record, file_info): record
                    for record in image_names
                }

                # 完了したタスクを順次処理
                for future in as_completed(future_to_record):
                    # 中断チェック
                    if self._check_cancellation():
                        self._logger.info(f"マルチスレッド処理中断: {file_info['file_name']}")
                        # 残りのタスクをキャンセル
                        for remaining_future in future_to_record:
                            remaining_future.cancel()
                        break

                    record = future_to_record[future]
                    try:
                        converted_files = future.result()
                        if converted_files:
                            converted_images.extend(converted_files)

                        # プログレス更新
                        self._update_progress()

                    except Exception as e:
                        self._logger.error(f"スレッド内エラー: {record.get('image_name', '不明')} - {e}")

        except Exception as e:
            self._logger.error(f"マルチスレッド処理エラー: {e}")
            return []

        elapsed_time = time.time() - start_time
        if not self._is_cancelled:
            self._logger.info(f"マルチスレッド処理完了: {file_info['file_name']} - "
                            f"変換画像数: {len(converted_images)}, 処理時間: {elapsed_time:.2f}秒")

        return converted_images

    def _process_single_image_thread_safe(self, record: Dict[str, str], file_info: Dict[str, str]) -> List[str]:
        """
        スレッドセーフな単一画像処理

        Args:
            record: 画像名情報
            file_info: ファイル情報

        Returns:
            変換された画像ファイルのパスのリスト
        """
        try:
            return self._process_single_image(record, file_info)
        except Exception as e:
            # スレッド内でのエラーハンドリング
            with self._thread_lock:
                self._logger.error(f"スレッド内画像処理エラー: {record.get('image_name', '不明')} - {e}")
            return []

    def _update_progress(self):
        """プログレス更新（スレッドセーフ）"""
        with self._thread_lock:
            self._progress_counter += 1
            progress = (self._progress_counter / self._total_images) * 100
            if self._progress_counter % 10 == 0 or self._progress_counter == self._total_images:
                self._logger.info(f"処理進捗: {self._progress_counter}/{self._total_images} ({progress:.1f}%)")

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

        self._logger.debug(f"処理対象: row_index={row_text}, image_name={image_name}")

        # コード抽出
        code = self._extract_code_from_row_index(row_text)
        if not code:
            return []

        if code not in self._config.width_map:
            self._logger.warning(f"幅未定義: {code} - スキップ: {image_name}")
            return []

        sizes = self._config.width_map[code]

        # 入力ファイル確認
        input_file = image_utils.find_input_image(image_name)
        if not input_file:
            self._logger.error(f"入力ファイルが存在しません: {image_name} (jpg/png/webp)")
            # 存在しない画像名をファイルに記録
            record_missing_image(image_name, file_info['file_name_without_ext'], self._logger)
            return []

        self._logger.debug(f"入力ファイル発見: {input_file}")

        # 幅ごとにWebP変換
        converted_files = []
        for size in sizes:
            # 中断チェック
            if self._check_cancellation():
                self._logger.debug(f"画像変換が中断されました: {image_name}")
                break

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
            self._logger.debug(f"スキップ: {image_name} - {size}px - 出力ファイルが既に存在")
            return output_file

        self._logger.debug(f"変換開始: {input_file} → {output_file} (width={size[0]} height={size[1]})")

        # Pillowを使用して変換（WebP形式の場合はリサイズのみ）
        success = image_utils.convert_image_with_pillow(input_file, size, output_file)

        if success:
            self._logger.debug(f"変換成功: {image_name} - {size}px")
            return output_file
        else:
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
            self._logger.warning(f"コード抽出失敗: {row_index}")
            return None

        return code_match.group(1)
