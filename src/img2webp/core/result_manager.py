"""
結果管理モジュール
処理結果の保存・出力を担当
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import logging

from ..config.loader import config_loader


class ResultManager:
    """処理結果の保存・管理を担当するクラス"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._config = config_loader.get_directories()

    def save_results(self, all_image_names: List[Dict[str, str]], all_converted_images: List[str]) -> None:
        """
        処理結果をファイルに保存

        Args:
            all_image_names: 全ファイルの画像名情報
            all_converted_images: 変換された画像ファイルのパス一覧
        """
        self._save_image_names_json(all_image_names)
        self._save_converted_images_list(all_converted_images)

    def _save_image_names_json(self, all_image_names: List[Dict[str, str]]) -> None:
        """
        画像名情報をJSONファイルに保存

        Args:
            all_image_names: 全ファイルの画像名情報
        """
        log_dir = Path(self._config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        json_file = log_dir / "all_image_names.json"

        try:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(all_image_names, f, ensure_ascii=False, indent=2)

            self._logger.info(f"画像名JSON出力完了: {json_file}")

        except Exception as e:
            self._logger.error(f"JSON出力失敗: {json_file} - {e}")
            raise

    def _save_converted_images_list(self, all_converted_images: List[str]) -> None:
        """
        変換済み画像一覧をテキストファイルに保存

        Args:
            all_converted_images: 変換された画像ファイルのパス一覧
        """
        log_dir = Path(self._config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        list_file = log_dir / "all_converted_images.txt"

        try:
            with open(list_file, "w", encoding="utf-8") as f:
                f.write("\n".join(all_converted_images))

            self._logger.info(f"変換済み画像一覧出力完了: {list_file} - 総数: {len(all_converted_images)}")

        except Exception as e:
            self._logger.error(f"変換済み画像一覧出力失敗: {list_file} - {e}")
            raise

    def create_summary_report(self,
                            docx_files: List[str],
                            all_converted_images: List[str],
                            missing_images_count: int) -> Dict[str, Any]:
        """
        処理結果のサマリーレポートを作成

        Args:
            docx_files: 処理対象のDOCXファイル一覧
            all_converted_images: 変換された画像ファイルのパス一覧
            missing_images_count: 存在しない画像の数

        Returns:
            サマリーレポートの辞書
        """
        summary = {
            "total_docx_files": len(docx_files),
            "total_converted_images": len(all_converted_images),
            "missing_images_count": missing_images_count,
            "processed_files": []
        }

        # ファイル別の統計を作成
        for docx_file in docx_files:
            file_stem = Path(docx_file).stem
            output_dir = Path(self._config.output_base_dir) / file_stem

            if output_dir.exists():
                webp_files = list(output_dir.glob("*.webp"))
                file_info = {
                    "file_name": Path(docx_file).name,
                    "output_directory": str(output_dir),
                    "converted_images_count": len(webp_files)
                }
            else:
                file_info = {
                    "file_name": Path(docx_file).name,
                    "output_directory": str(output_dir),
                    "converted_images_count": 0
                }

            summary["processed_files"].append(file_info)

        return summary

    def save_summary_report(self, summary: Dict[str, Any]) -> None:
        """
        サマリーレポートをJSONファイルに保存

        Args:
            summary: サマリーレポートの辞書
        """
        log_dir = Path(self._config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        summary_file = log_dir / "processing_summary.json"

        try:
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            self._logger.info(f"サマリーレポート出力完了: {summary_file}")

        except Exception as e:
            self._logger.error(f"サマリーレポート出力失敗: {summary_file} - {e}")
            raise
