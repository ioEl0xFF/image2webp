#!/usr/bin/env python3
"""
設定画面GUI
JSONベースの設定システムを使用してconfig.jsonの設定値をGUIで編集可能にする
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import sys
from pathlib import Path

# srcディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config_loader import config_loader
    from src import config
except ImportError:
    try:
        # スタンドアロンで実行された場合は、srcディレクトリから直接インポート
        sys.path.insert(0, 'src')
        from config_loader import config_loader
        import config
    except ImportError:
        # 最後の手段として、相対パスで試行
        import importlib.util
        spec = importlib.util.spec_from_file_location("config_loader", "src/config_loader.py")
        config_loader_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_loader_module)
        config_loader = config_loader_module.config_loader

        spec2 = importlib.util.spec_from_file_location("config", "src/config.py")
        config = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(config)


class ConfigEditorWindow:
    """JSON設定編集ウィンドウ"""

    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("設定編集")
        self.window.geometry("800x900")
        self.window.minsize(700, 800)

        # モーダルウィンドウにする
        self.window.transient(parent)
        self.window.grab_set()

        # 設定値を保持する変数
        self._init_variables()

        # UIを構築
        self._create_widgets()

        # 現在の設定値を読み込み
        self._load_current_config()

        # ウィンドウを中央に配置
        self._center_window()

    def _init_variables(self):
        """設定値を保持する変数を初期化"""
        # ディレクトリ設定
        self.docx_directory = tk.StringVar(value=config_loader.get("directories.docx_directory", "docxs"))
        self.output_base_dir = tk.StringVar(value=config_loader.get("directories.output_base_dir", "output"))
        self.images_dir = tk.StringVar(value=config_loader.get("directories.images_dir", "images"))
        self.html_dir = tk.StringVar(value=config_loader.get("directories.html_dir", "html"))

        # 画像処理設定
        self.webp_quality = tk.IntVar(value=config_loader.get("image_processing.webp_quality", 100))
        self.webp_method = tk.IntVar(value=config_loader.get("image_processing.webp_method", 6))
        self.webp_lossless = tk.BooleanVar(value=config_loader.get("image_processing.webp_lossless", True))

        # ログ設定
        self.log_dir = tk.StringVar(value=config_loader.get("directories.log_dir", ".logs"))
        self.log_file = tk.StringVar(value=config_loader.get("logging.log_file", "LOG.log"))
        self.log_level = tk.StringVar(value=config_loader.get("logging.log_level", "INFO"))

        # 正規表現パターン（テキストエリア用）
        self.image_pattern = tk.StringVar(value=config_loader.get("patterns.image_pattern", ""))
        self.code_pattern = tk.StringVar(value=config_loader.get("patterns.code_pattern", ""))

        # サポートされる拡張子
        extensions = config_loader.get("image_processing.supported_extensions", [])
        self.supported_extensions = tk.StringVar(value=", ".join(extensions))

    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # グリッドの重み設定
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)  # ノートブック部分を拡張可能にする

        # タイトル
        title_label = ttk.Label(main_frame, text="設定編集 (JSON)", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))

        # ノートブック（タブ）を作成
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))

        # 各タブを作成
        self._create_directory_tab()
        self._create_image_processing_tab()
        self._create_log_tab()
        self._create_pattern_tab()
        self._create_advanced_tab()

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0))

        ttk.Button(button_frame, text="適用", command=self._apply_config).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="保存して閉じる", command=self._save_and_close).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="リセット", command=self._reset_config).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(button_frame, text="キャンセル", command=self._cancel).grid(row=0, column=3)

    def _create_directory_tab(self):
        """ディレクトリ設定タブを作成"""
        dir_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(dir_frame, text="ディレクトリ")

        dir_frame.columnconfigure(1, weight=1)

        # DOCXディレクトリ
        ttk.Label(dir_frame, text="DOCXディレクトリ:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_frame, textvariable=self.docx_directory).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

        # 出力ベースディレクトリ
        ttk.Label(dir_frame, text="出力ベースディレクトリ:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_frame, textvariable=self.output_base_dir).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

        # 画像ディレクトリ
        ttk.Label(dir_frame, text="画像ディレクトリ:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_frame, textvariable=self.images_dir).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

        # HTMLディレクトリ
        ttk.Label(dir_frame, text="HTMLディレクトリ:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_frame, textvariable=self.html_dir).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

        # ログディレクトリ
        ttk.Label(dir_frame, text="ログディレクトリ:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_frame, textvariable=self.log_dir).grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

    def _create_image_processing_tab(self):
        """画像処理設定タブを作成"""
        img_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(img_frame, text="画像処理")

        img_frame.columnconfigure(1, weight=1)

        # WebP品質
        ttk.Label(img_frame, text="WebP品質 (1-100):").grid(row=0, column=0, sticky=tk.W, pady=5)
        quality_frame = ttk.Frame(img_frame)
        quality_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        quality_frame.columnconfigure(0, weight=1)

        ttk.Scale(quality_frame, from_=1, to=100, variable=self.webp_quality,
                 orient=tk.HORIZONTAL).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Label(quality_frame, textvariable=self.webp_quality).grid(row=0, column=1, padx=(10, 0))

        # WebP圧縮方法
        ttk.Label(img_frame, text="WebP圧縮方法 (0-6):").grid(row=1, column=0, sticky=tk.W, pady=5)
        method_frame = ttk.Frame(img_frame)
        method_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        method_frame.columnconfigure(0, weight=1)

        ttk.Scale(method_frame, from_=0, to=6, variable=self.webp_method,
                 orient=tk.HORIZONTAL).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Label(method_frame, textvariable=self.webp_method).grid(row=0, column=1, padx=(10, 0))

        # WebPロスレス
        ttk.Checkbutton(img_frame, text="WebPロスレス圧縮",
                       variable=self.webp_lossless).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # サポートする拡張子
        ttk.Label(img_frame, text="サポートする拡張子:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(img_frame, textvariable=self.supported_extensions).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        ttk.Label(img_frame, text="カンマ区切りで入力", font=('Arial', 8)).grid(row=4, column=1, sticky=tk.W, padx=(10, 0))

    def _create_log_tab(self):
        """ログ設定タブを作成"""
        log_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(log_frame, text="ログ")

        log_frame.columnconfigure(1, weight=1)

        # ログファイル名
        ttk.Label(log_frame, text="ログファイル名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(log_frame, textvariable=self.log_file).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

        # ログレベル
        ttk.Label(log_frame, text="ログレベル:").grid(row=1, column=0, sticky=tk.W, pady=5)
        log_level_combo = ttk.Combobox(log_frame, textvariable=self.log_level,
                                      values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                      state="readonly")
        log_level_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

    def _create_pattern_tab(self):
        """パターン設定タブを作成"""
        pattern_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(pattern_frame, text="パターン")

        pattern_frame.columnconfigure(0, weight=1)
        pattern_frame.rowconfigure(1, weight=1)
        pattern_frame.rowconfigure(3, weight=1)

        # 画像パターン
        ttk.Label(pattern_frame, text="画像抽出パターン（正規表現）:").grid(row=0, column=0, sticky=tk.W, pady=5)

        image_pattern_frame = ttk.Frame(pattern_frame)
        image_pattern_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        image_pattern_frame.columnconfigure(0, weight=1)
        image_pattern_frame.rowconfigure(0, weight=1)

        self.image_pattern_text = scrolledtext.ScrolledText(image_pattern_frame, height=8, wrap=tk.WORD)
        self.image_pattern_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # コードパターン
        ttk.Label(pattern_frame, text="コード抽出パターン（正規表現）:").grid(row=2, column=0, sticky=tk.W, pady=5)

        code_pattern_frame = ttk.Frame(pattern_frame)
        code_pattern_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        code_pattern_frame.columnconfigure(0, weight=1)
        code_pattern_frame.rowconfigure(0, weight=1)

        self.code_pattern_text = scrolledtext.ScrolledText(code_pattern_frame, height=4, wrap=tk.WORD)
        self.code_pattern_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def _create_advanced_tab(self):
        """詳細設定タブを作成"""
        advanced_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(advanced_frame, text="詳細")

        advanced_frame.columnconfigure(0, weight=1)
        advanced_frame.rowconfigure(1, weight=1)

        # 説明
        ttk.Label(advanced_frame, text="WIDTH_MAPとMIN_WIDTH_SIZE_MAPの詳細設定",
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, pady=(0, 10))

        # 設定表示エリア
        self.advanced_text = scrolledtext.ScrolledText(advanced_frame, height=20, state=tk.DISABLED)
        self.advanced_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 注意事項
        note_text = ("注意: WIDTH_MAPとMIN_WIDTH_SIZE_MAPは複雑な辞書構造のため、\n"
                    "現在は表示のみ対応しています。編集が必要な場合は、\n"
                    "config.jsonファイルを直接編集してください。")
        ttk.Label(advanced_frame, text=note_text, foreground="red",
                 font=('Arial', 9)).grid(row=2, column=0, pady=(10, 0))

    def _load_current_config(self):
        """現在の設定値を読み込み"""
        # テキストエリアに正規表現パターンを設定
        self.image_pattern_text.insert(1.0, config_loader.get("patterns.image_pattern", ""))
        self.code_pattern_text.insert(1.0, config_loader.get("patterns.code_pattern", ""))

        # 詳細設定を表示
        self._display_advanced_config()

    def _display_advanced_config(self):
        """詳細設定を表示"""
        self.advanced_text.config(state=tk.NORMAL)
        self.advanced_text.delete(1.0, tk.END)

        # WIDTH_MAPを表示
        width_map = config_loader.get_width_map()
        self.advanced_text.insert(tk.END, "WIDTH_MAP:\n")
        for key, value in width_map.items():
            self.advanced_text.insert(tk.END, f"  {key}: {value}\n")

        self.advanced_text.insert(tk.END, "\nMIN_WIDTH_SIZE_MAP:\n")
        min_width_map = config_loader.get_min_width_size_map()
        for key, value in min_width_map.items():
            self.advanced_text.insert(tk.END, f"  {key}:\n")
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    self.advanced_text.insert(tk.END, f"    {sub_key}: {sub_value}\n")
            else:
                self.advanced_text.insert(tk.END, f"    {value}\n")

        self.advanced_text.config(state=tk.DISABLED)

    def _apply_config(self):
        """設定を適用"""
        try:
            # バックアップを作成
            self._create_backup()

            # 設定値を更新
            config_loader.set("directories.docx_directory", self.docx_directory.get())
            config_loader.set("directories.output_base_dir", self.output_base_dir.get())
            config_loader.set("directories.images_dir", self.images_dir.get())
            config_loader.set("directories.html_dir", self.html_dir.get())
            config_loader.set("directories.log_dir", self.log_dir.get())

            config_loader.set("image_processing.webp_quality", self.webp_quality.get())
            config_loader.set("image_processing.webp_method", self.webp_method.get())
            config_loader.set("image_processing.webp_lossless", self.webp_lossless.get())

            config_loader.set("logging.log_file", self.log_file.get())
            config_loader.set("logging.log_level", self.log_level.get())

            # 正規表現パターンを更新
            config_loader.set("patterns.image_pattern", self.image_pattern_text.get(1.0, tk.END).strip())
            config_loader.set("patterns.code_pattern", self.code_pattern_text.get(1.0, tk.END).strip())

            # サポートする拡張子を更新
            extensions = [ext.strip() for ext in self.supported_extensions.get().split(",")]
            config_loader.set("image_processing.supported_extensions", [ext for ext in extensions if ext])

            # JSONファイルに保存
            config_loader.save_config()

            # configモジュールを再読み込み
            config.reload_config()

            messagebox.showinfo("成功", "設定を適用しました\n（バックアップ: config.json.backup）")

        except Exception as e:
            messagebox.showerror("エラー", f"設定の適用に失敗しました:\n{str(e)}")

    def _create_backup(self):
        """config.jsonのバックアップを作成"""
        config_path = Path("config.json")
        backup_path = Path("config.json.backup")

        if config_path.exists():
            import shutil
            shutil.copy2(config_path, backup_path)

    def _reset_config(self):
        """設定をリセット"""
        if messagebox.askyesno("確認", "設定を初期値にリセットしますか？"):
            # 初期値に戻す
            self.docx_directory.set("docxs")
            self.output_base_dir.set("output")
            self.images_dir.set("images")
            self.html_dir.set("html")
            self.log_dir.set(".logs")

            self.webp_quality.set(100)
            self.webp_method.set(6)
            self.webp_lossless.set(True)

            self.log_file.set("LOG.log")
            self.log_level.set("INFO")

            self.supported_extensions.set("webp, WEBP, jpg, png, JPG, PNG")

            # テキストエリアをリセット
            self.image_pattern_text.delete(1.0, tk.END)
            self.code_pattern_text.delete(1.0, tk.END)

            # デフォルトパターンを設定
            default_image_pattern = (
                r"(?:"
                r"[＜<〈]画像(?:名|\d*)?(?:（[^）]*）)?[＞>〉]\s*([a-zA-Z0-9\-_]+)"
                r"|"
                r"画像名[:：]\s*([a-zA-Z0-9\-_]+)"
                r")"
            )
            default_code_pattern = r"^(COMFRPTC\d+|GSTFRPTA\d+|THUMBNAIL)"

            self.image_pattern_text.insert(1.0, default_image_pattern)
            self.code_pattern_text.insert(1.0, default_code_pattern)

    def _save_and_close(self):
        """保存して閉じる"""
        self._apply_config()
        self.window.destroy()

    def _cancel(self):
        """キャンセル"""
        self.window.destroy()

    def _center_window(self):
        """ウィンドウを中央に配置"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")


def main():
    """テスト用メイン関数"""
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを非表示にする

    config_window = ConfigEditorWindow(root)

    root.mainloop()


if __name__ == "__main__":
    main()