#!/usr/bin/env python3
"""
img2webp GUI版メインエントリーポイント
DOCXファイルから画像名を抽出し、WebP形式に変換するGUIアプリケーション
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import json
from pathlib import Path

from .processor import ProcessorThread
from ..config.defaults import WEBP_QUALITY, LOG_DIR
from ..config.loader import config_loader
from .config_editor import ConfigEditorWindow


class Img2WebpGUI:
    """img2webp GUIアプリケーション"""

    def __init__(self, root):
        self.root = root
        self.root.title("img2webp - 画像変換ツール")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)

        # 設定値
        self.docx_dir = tk.StringVar()
        self.images_dir = tk.StringVar()
        self.html_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.webp_quality = tk.IntVar(value=WEBP_QUALITY)

        # マルチスレッド設定
        self.enable_multithreading = tk.BooleanVar(value=config_loader.get("image_processing.enable_multithreading", True))
        self.max_workers = tk.IntVar(value=config_loader.get("image_processing.max_workers", 4))

        # 処理制御
        self.is_processing = False
        self.processor_thread = None
        self.conversion_thread = None
        self.log_queue = queue.Queue()
        self.error_count = 0

        # デフォルト値設定
        self._set_default_paths()

        # UI構築
        self._create_widgets()
        self._load_settings()

        # キーバインドの設定
        self._setup_key_bindings()

        # ログキューの監視開始
        self._check_log_queue()

    def _set_default_paths(self):
        """デフォルトパスを設定"""
        current_dir = Path.cwd()
        self.docx_dir.set(str(current_dir / config_loader.get("directories.docx_directory", "docxs")))
        self.images_dir.set(str(current_dir / config_loader.get("directories.images_dir", "images")))
        self.html_dir.set(str(current_dir / config_loader.get("directories.html_dir", "html")))
        self.output_dir.set(str(current_dir / config_loader.get("directories.output_base_dir", "output")))

    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(8, weight=1)

        # タイトル
        title_label = ttk.Label(main_frame, text="img2webp - 画像変換ツール",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # ファイル選択セクション
        self._create_file_selection_section(main_frame)

        # 設定セクション
        self._create_settings_section(main_frame)

        # 制御ボタンセクション
        self._create_control_section(main_frame)

        # 進捗バー
        self.progress_var = tk.StringVar(value="準備完了")
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 5))

        progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_label.grid(row=7, column=0, columnspan=3, pady=(0, 10))

        # 詳細進捗情報
        self.detail_progress_var = tk.StringVar(value="")
        detail_progress_label = ttk.Label(main_frame, textvariable=self.detail_progress_var,
                                        font=('Arial', 9), foreground='gray')
        detail_progress_label.grid(row=7, column=0, columnspan=3, pady=(25, 0))

        # ログ表示セクション
        self._create_log_section(main_frame)

    def _create_file_selection_section(self, parent):
        """ファイル選択セクションを作成"""
        # セクションタイトル
        file_frame = ttk.LabelFrame(parent, text="ディレクトリ設定", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        # DOCXディレクトリ
        ttk.Label(file_frame, text="DOCXファイル:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.docx_entry = ttk.Entry(file_frame, textvariable=self.docx_dir, width=50)
        self.docx_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        self.docx_entry.bind('<FocusOut>', self._on_path_change)
        self.docx_button = ttk.Button(file_frame, text="選択", command=lambda: self._select_directory(self.docx_dir))
        self.docx_button.grid(row=0, column=2)

        # 画像ディレクトリ
        ttk.Label(file_frame, text="画像ファイル:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.images_entry = ttk.Entry(file_frame, textvariable=self.images_dir, width=50)
        self.images_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        self.images_entry.bind('<FocusOut>', self._on_path_change)
        self.images_button = ttk.Button(file_frame, text="選択", command=lambda: self._select_directory(self.images_dir))
        self.images_button.grid(row=1, column=2)

        # HTMLディレクトリ（オプション）
        ttk.Label(file_frame, text="HTMLファイル:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.html_entry = ttk.Entry(file_frame, textvariable=self.html_dir, width=50)
        self.html_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        self.html_entry.bind('<FocusOut>', self._on_path_change)
        self.html_button = ttk.Button(file_frame, text="選択", command=lambda: self._select_directory(self.html_dir))
        self.html_button.grid(row=2, column=2)

        # 出力ディレクトリ
        ttk.Label(file_frame, text="出力先:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.output_entry = ttk.Entry(file_frame, textvariable=self.output_dir, width=50)
        self.output_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        self.output_entry.bind('<FocusOut>', self._on_path_change)
        self.output_button = ttk.Button(file_frame, text="選択", command=lambda: self._select_directory(self.output_dir))
        self.output_button.grid(row=3, column=2)

    def _create_settings_section(self, parent):
        """設定セクションを作成"""
        settings_frame = ttk.LabelFrame(parent, text="変換設定", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # WebP品質設定
        ttk.Label(settings_frame, text="WebP品質:").grid(row=0, column=0, sticky=tk.W)
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

        self.quality_scale = ttk.Scale(quality_frame, from_=1, to=100, variable=self.webp_quality,
                 orient=tk.HORIZONTAL, length=200, command=self._on_quality_change)
        self.quality_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Label(quality_frame, textvariable=self.webp_quality).grid(row=0, column=1, padx=(10, 0))

        quality_frame.columnconfigure(0, weight=1)

        # 区切り線
        ttk.Separator(settings_frame, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 10))

        # マルチスレッド設定セクション
        ttk.Label(settings_frame, text="マルチスレッド処理:", font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # マルチスレッド有効化チェックボックス
        self.multithread_enable_frame = ttk.Frame(settings_frame)
        self.multithread_enable_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)

        ttk.Checkbutton(self.multithread_enable_frame, text="マルチスレッド処理を有効にする",
                       variable=self.enable_multithreading,
                       command=self._on_multithread_toggle).grid(row=0, column=0, sticky=tk.W)

        # CPU情報表示
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        ttk.Label(self.multithread_enable_frame, text=f"(システムCPU: {cpu_count}コア)",
                 font=('Arial', 8), foreground='gray').grid(row=0, column=1, padx=(10, 0), sticky=tk.W)

        # 最大スレッド数設定
        ttk.Label(settings_frame, text="最大スレッド数:").grid(row=4, column=0, sticky=tk.W, pady=(5, 2))

        self.workers_frame = ttk.Frame(settings_frame)
        self.workers_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(5, 2))
        self.workers_frame.columnconfigure(0, weight=1)

        self.workers_scale = ttk.Scale(self.workers_frame, from_=1, to=16, variable=self.max_workers,
                                      orient=tk.HORIZONTAL, length=200, command=self._on_workers_change)
        self.workers_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.workers_label = ttk.Label(self.workers_frame, text=f"{self.max_workers.get()}")
        self.workers_label.grid(row=0, column=1, padx=(10, 0))

        # 推奨値表示
        recommended_workers = min(4, cpu_count)
        ttk.Label(settings_frame, text=f"推奨値: {recommended_workers} (CPUコア数以下)",
                 font=('Arial', 8), foreground='gray').grid(row=5, column=1, sticky=tk.W, padx=(10, 0))

        # 初期状態の設定（UI作成完了後に実行）
        self.root.after_idle(self._on_multithread_toggle)

    def _create_control_section(self, parent):
        """制御ボタンセクションを作成"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=6, column=0, columnspan=3, pady=(10, 10))

        self.start_button = ttk.Button(control_frame, text="変換開始",
                                      command=self._start_conversion, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, padx=(0, 10))

        self.stop_button = ttk.Button(control_frame, text="停止 (Ctrl+C)",
                                     command=self._stop_conversion, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))

        # ツールチップを追加
        self._create_tooltip(self.stop_button, "処理を安全に中断します\nキーボード: Ctrl+C または ESC")

        ttk.Button(control_frame, text="ログクリア",
                  command=self._clear_log).grid(row=0, column=2, padx=(0, 10))


        ttk.Button(control_frame, text="詳細設定",
                  command=self._open_config_editor).grid(row=0, column=3)

    def _create_log_section(self, parent):
        """ログ表示セクションを作成"""
        log_frame = ttk.LabelFrame(parent, text="処理ログ", padding="5")
        log_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # タブ作成
        self.log_notebook = ttk.Notebook(log_frame)
        self.log_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 全ログタブ
        self.all_log_frame = ttk.Frame(self.log_notebook)
        self.log_notebook.add(self.all_log_frame, text="全ログ")

        self.log_text = scrolledtext.ScrolledText(self.all_log_frame, height=15, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.all_log_frame.columnconfigure(0, weight=1)
        self.all_log_frame.rowconfigure(0, weight=1)

        # エラーログタブ
        self.error_log_frame = ttk.Frame(self.log_notebook)
        self.log_notebook.add(self.error_log_frame, text="エラー")

        self.error_log_text = scrolledtext.ScrolledText(self.error_log_frame, height=15, state=tk.DISABLED)
        self.error_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.error_log_frame.columnconfigure(0, weight=1)
        self.error_log_frame.rowconfigure(0, weight=1)

        # ログテキストの色設定（両方のテキストエリアに適用）
        for text_widget in [self.log_text, self.error_log_text]:
            text_widget.tag_configure("info", foreground="black")
            text_widget.tag_configure("warning", foreground="orange")
            text_widget.tag_configure("error", foreground="red")
            text_widget.tag_configure("success", foreground="green")

    def _select_directory(self, var):
        """ディレクトリ選択ダイアログ"""
        directory = filedialog.askdirectory(initialdir=var.get())
        if directory:
            var.set(directory)
            # ディレクトリが変更されたら自動保存
            if not self.is_processing:
                self._auto_save_all_settings()

    def _start_conversion(self):
        """変換処理開始"""
        if self.is_processing:
            return

        # 入力検証
        if not self._validate_inputs():
            return

        # UI状態更新
        self.is_processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(10)
        self.progress_var.set("処理中...")
        self.detail_progress_var.set("処理を開始しています...")

        # 設定コントロールを無効化
        self._disable_settings_controls()

        # ログクリア
        self._clear_log()
        # 全ログタブに切り替え
        self.log_notebook.select(0)
        self._add_log("=== 変換処理を開始します ===", "info")

        # 別スレッドで処理実行
        self.conversion_thread = threading.Thread(target=self._run_conversion)
        self.conversion_thread.daemon = True
        self.conversion_thread.start()

        # 進捗監視を開始
        self._monitor_progress()

    def _stop_conversion(self):
        """変換処理停止"""
        if self.processor_thread and hasattr(self.processor_thread, 'cancel'):
            self._add_log("停止要求を受け付けました。処理を安全に終了しています...", "warning")
            self.progress_var.set("停止中...")
            self.detail_progress_var.set("現在の処理を完了してから停止します")
            self.processor_thread.cancel()

            # 停止ボタンを無効化（重複クリック防止）
            self.stop_button.config(state=tk.DISABLED)
        else:
            self._reset_ui_state()

    def _run_conversion(self):
        """変換処理を実行（別スレッド）"""
        try:
            # GUI設定を取得
            gui_settings = self._get_gui_settings()

            # プロセッサースレッドを作成・実行
            self.processor_thread = ProcessorThread(self.log_queue, gui_settings)
            self.processor_thread.start()

            # 処理完了を待機
            self.processor_thread.join()

            # 例外が発生していた場合は再発生
            if self.processor_thread.exception:
                raise self.processor_thread.exception

            self.log_queue.put(("=== 変換処理が完了しました ===", "success"))

        except Exception as e:
            self.log_queue.put((f"エラー: {str(e)}", "error"))
        finally:
            # UI状態をリセット
            self.root.after(0, self._reset_ui_state)

    def _get_gui_settings(self):
        """GUI設定を取得"""
        return {
            'docx_dir': self.docx_dir.get(),
            'images_dir': self.images_dir.get(),
            'html_dir': self.html_dir.get(),
            'output_dir': self.output_dir.get(),
            'webp_quality': self.webp_quality.get(),
            'enable_multithreading': self.enable_multithreading.get(),
            'max_workers': self.max_workers.get()
        }

    def _validate_inputs(self):
        """入力値を検証"""
        if not os.path.exists(self.docx_dir.get()):
            messagebox.showerror("エラー", "DOCXディレクトリが存在しません")
            return False

        if not os.path.exists(self.images_dir.get()):
            messagebox.showerror("エラー", "画像ディレクトリが存在しません")
            return False

        return True

    def _setup_key_bindings(self):
        """キーバインドを設定"""
        # Ctrl+C で処理中断（処理中のみ有効）
        self.root.bind('<Control-c>', self._on_ctrl_c)
        # ESC キーでも処理中断
        self.root.bind('<Escape>', self._on_escape)

    def _on_ctrl_c(self, event):
        """Ctrl+C キー処理"""
        if self.is_processing:
            self._stop_conversion()

    def _on_escape(self, event):
        """Escape キー処理"""
        if self.is_processing:
            self._stop_conversion()

    def _monitor_progress(self):
        """進捗を監視して表示を更新"""
        if self.processor_thread and hasattr(self.processor_thread, 'get_progress_info'):
            progress_info = self.processor_thread.get_progress_info()

            if progress_info['total_files'] > 0:
                # プログレスバーを確定的モードに変更
                if self.progress_bar['mode'] != 'determinate':
                    self.progress_bar.stop()
                    self.progress_bar.config(mode='determinate')
                    self.progress_bar['maximum'] = progress_info['total_files']

                # 進捗を更新
                self.progress_bar['value'] = progress_info['current_file']

                if progress_info['current_file'] > 0:
                    self.progress_var.set(f"処理中 ({progress_info['current_file']}/{progress_info['total_files']})")
                    self.detail_progress_var.set(f"ファイル処理中... {progress_info['current_file']}/{progress_info['total_files']}")

                # キャンセル状態の確認
                if progress_info['is_cancelled']:
                    self.progress_var.set("停止中...")
                    self.detail_progress_var.set("処理を安全に停止しています...")

        # 処理中なら再度監視をスケジュール
        if self.is_processing:
            self.root.after(500, self._monitor_progress)

    def _reset_ui_state(self):
        """UI状態をリセット"""
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_var.set("準備完了")
        self.detail_progress_var.set("")

        # 設定コントロールを再度有効化
        self._enable_settings_controls()

    def _enable_settings_controls(self):
        """設定コントロールを有効化"""
        # エントリーフィールドを有効化
        self.docx_entry.config(state=tk.NORMAL)
        self.images_entry.config(state=tk.NORMAL)
        self.html_entry.config(state=tk.NORMAL)
        self.output_entry.config(state=tk.NORMAL)

        # ディレクトリ選択ボタンを有効化
        self.docx_button.config(state=tk.NORMAL)
        self.images_button.config(state=tk.NORMAL)
        self.html_button.config(state=tk.NORMAL)
        self.output_button.config(state=tk.NORMAL)

        # スケールコントロールを有効化
        self.quality_scale.config(state=tk.NORMAL)

        # マルチスレッド設定を有効化（条件付き）
        self._on_multithread_toggle()

    def _disable_settings_controls(self):
        """設定コントロールを無効化"""
        # エントリーフィールドを無効化
        self.docx_entry.config(state=tk.DISABLED)
        self.images_entry.config(state=tk.DISABLED)
        self.html_entry.config(state=tk.DISABLED)
        self.output_entry.config(state=tk.DISABLED)

        # ディレクトリ選択ボタンを無効化
        self.docx_button.config(state=tk.DISABLED)
        self.images_button.config(state=tk.DISABLED)
        self.html_button.config(state=tk.DISABLED)
        self.output_button.config(state=tk.DISABLED)

        # スケールコントロールを無効化
        self.quality_scale.config(state=tk.DISABLED)

        # マルチスレッド設定を無効化
        if hasattr(self, 'multithread_enable_frame'):
            for child in self.multithread_enable_frame.winfo_children():
                if isinstance(child, ttk.Checkbutton):
                    child.config(state=tk.DISABLED)

        if hasattr(self, 'workers_scale'):
            self.workers_scale.config(state=tk.DISABLED)
            self.workers_label.config(foreground='gray')

    def _check_log_queue(self):
        """ログキューを監視してログを表示"""
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                self._add_log(message, level)
        except queue.Empty:
            pass
        finally:
            # 100ms後に再度チェック
            self.root.after(100, self._check_log_queue)

    def _add_log(self, message, level="info"):
        """ログを追加"""
        # 全ログタブに追加
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        # エラーまたは警告の場合はエラータブにも追加
        if level in ["error", "warning"]:
            self.error_log_text.config(state=tk.NORMAL)
            self.error_log_text.insert(tk.END, f"{message}\n", level)
            self.error_log_text.see(tk.END)
            self.error_log_text.config(state=tk.DISABLED)

            # エラーカウントを増加
            self.error_count += 1

            # エラータブのタイトルを更新
            self._update_error_tab_title()

    def _clear_log(self):
        """ログをクリア"""
        # 全ログタブをクリア
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # エラーログタブをクリア
        self.error_log_text.config(state=tk.NORMAL)
        self.error_log_text.delete(1.0, tk.END)
        self.error_log_text.config(state=tk.DISABLED)

        # エラーカウントをリセット
        self.error_count = 0
        self._update_error_tab_title()

    def _update_error_tab_title(self):
        """エラータブのタイトルを更新"""
        if self.error_count > 0:
            title = f"エラー ({self.error_count})"
        else:
            title = "エラー"

        # タブのテキストを更新
        self.log_notebook.tab(1, text=title)

    def _save_settings(self):
        """設定を保存"""
        try:
            # JSONコンフィグに保存
            config_loader.set("directories.docx_directory", Path(self.docx_dir.get()).name)
            config_loader.set("directories.images_dir", Path(self.images_dir.get()).name)
            config_loader.set("directories.html_dir", Path(self.html_dir.get()).name)
            config_loader.set("directories.output_base_dir", Path(self.output_dir.get()).name)
            config_loader.set("image_processing.webp_quality", self.webp_quality.get())

            # マルチスレッド設定も保存
            config_loader.set("image_processing.enable_multithreading", self.enable_multithreading.get())
            config_loader.set("image_processing.max_workers", self.max_workers.get())

            # 設定を保存
            config_loader.save_config()

            # 後方互換性のためgui_settings.jsonも保存
            settings = {
                "docx_dir": self.docx_dir.get(),
                "images_dir": self.images_dir.get(),
                "html_dir": self.html_dir.get(),
                "output_dir": self.output_dir.get(),
                "webp_quality": self.webp_quality.get()
            }
            with open("gui_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

            self._add_log("設定を保存しました", "success")
        except Exception as e:
            self._add_log(f"設定保存エラー: {e}", "error")

    def _load_settings(self):
        """設定を読み込み"""
        try:
            # まずJSONコンフィグから読み込み
            current_dir = Path.cwd()

            # 既存のgui_settings.jsonがあるかチェック（移行のため）
            if os.path.exists("gui_settings.json"):
                with open("gui_settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)

                self.docx_dir.set(settings.get("docx_dir", self.docx_dir.get()))
                self.images_dir.set(settings.get("images_dir", self.images_dir.get()))
                self.html_dir.set(settings.get("html_dir", self.html_dir.get()))
                self.output_dir.set(settings.get("output_dir", self.output_dir.get()))
                self.webp_quality.set(settings.get("webp_quality",
                    config_loader.get("image_processing.webp_quality", WEBP_QUALITY)))

                # マルチスレッド設定も読み込み
                self.enable_multithreading.set(settings.get("enable_multithreading",
                    config_loader.get("image_processing.enable_multithreading", True)))
                self.max_workers.set(settings.get("max_workers",
                    config_loader.get("image_processing.max_workers", 4)))
            else:
                # JSONコンフィグから読み込み
                self.docx_dir.set(str(current_dir / config_loader.get("directories.docx_directory", "docxs")))
                self.images_dir.set(str(current_dir / config_loader.get("directories.images_dir", "images")))
                self.html_dir.set(str(current_dir / config_loader.get("directories.html_dir", "html")))
                self.output_dir.set(str(current_dir / config_loader.get("directories.output_base_dir", "output")))
                self.webp_quality.set(config_loader.get("image_processing.webp_quality", WEBP_QUALITY))

                # マルチスレッド設定も読み込み
                self.enable_multithreading.set(config_loader.get("image_processing.enable_multithreading", True))
                self.max_workers.set(config_loader.get("image_processing.max_workers", 4))

        except Exception as e:
            self._add_log(f"設定読み込みエラー: {e}", "warning")

    def _open_config_editor(self):
        """設定編集ウィンドウを開く"""
        try:
            config_window = ConfigEditorWindow(self.root)
            # ウィンドウが閉じられるまで待機
            self.root.wait_window(config_window.window)

            # 設定が変更された可能性があるので、設定を再読み込み
            config_loader.reload_config()
            from ..config import defaults as config_module
            config_module.reload_config()

            # GUIの設定値も更新
            self._load_settings()

            # マルチスレッド表示も更新
            self._update_multithread_display()

            self._add_log("設定画面を閉じました。設定を再読み込みしました", "info")

        except Exception as e:
            self._add_log(f"設定画面エラー: {e}", "error")

    def _create_tooltip(self, widget, text):
        """ツールチップを作成"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = ttk.Label(tooltip, text=text, background="lightyellow",
                            relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()

            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _on_multithread_toggle(self):
        """マルチスレッド有効化状態の変更処理"""
        # UI要素が初期化されているかチェック
        if not hasattr(self, 'workers_scale') or self.workers_scale is None:
            return

        enabled = self.enable_multithreading.get()
        state = tk.NORMAL if enabled else tk.DISABLED

        # スレッド数設定の有効/無効を切り替え
        self.workers_scale.config(state=state)
        if enabled:
            self.workers_label.config(foreground='black')
        else:
            self.workers_label.config(foreground='gray')

        # 設定を自動保存
        self._auto_save_multithread_settings()

    def _on_workers_change(self, value):
        """スレッド数変更処理"""
        workers = int(float(value))
        self.workers_label.config(text=str(workers))

        # 設定を自動保存
        self._auto_save_multithread_settings()

    def _auto_save_multithread_settings(self):
        """マルチスレッド設定を自動保存"""
        try:
            # 設定を更新
            config_loader.set("image_processing.enable_multithreading", self.enable_multithreading.get())
            config_loader.set("image_processing.max_workers", self.max_workers.get())

            # 設定を保存
            config_loader.save_config()

            # UI初期化完了チェック
            if hasattr(self, 'progress_var') and self.progress_var is not None:
                # ステータスメッセージを表示（ログには出力しない）
                enabled = self.enable_multithreading.get()
                workers = self.max_workers.get()

                if enabled:
                    status_msg = f"マルチスレッド設定更新: 有効 ({workers}スレッド)"
                else:
                    status_msg = f"マルチスレッド設定更新: 無効"

                # 一時的にステータスを表示（3秒後に元に戻す）
                original_text = self.progress_var.get()
                self.progress_var.set(status_msg)
                self.root.after(3000, lambda: self.progress_var.set(original_text))

        except Exception as e:
            # UI初期化完了チェック
            if hasattr(self, 'log_text') and self.log_text is not None:
                self._add_log(f"マルチスレッド設定保存エラー: {e}", "error")
            else:
                # 初期化中のエラーは標準出力に表示
                print(f"マルチスレッド設定保存エラー: {e}")

    def _on_path_change(self, event=None):
        """パス変更時の自動保存処理"""
        if not self.is_processing:
            self._auto_save_all_settings()

    def _on_quality_change(self, value):
        """WebP品質変更時の自動保存処理"""
        if not self.is_processing:
            self._auto_save_all_settings()

    def _auto_save_all_settings(self):
        """全設定を自動保存"""
        try:
            # JSONコンフィグに保存
            config_loader.set("directories.docx_directory", Path(self.docx_dir.get()).name)
            config_loader.set("directories.images_dir", Path(self.images_dir.get()).name)
            config_loader.set("directories.html_dir", Path(self.html_dir.get()).name)
            config_loader.set("directories.output_base_dir", Path(self.output_dir.get()).name)
            config_loader.set("image_processing.webp_quality", self.webp_quality.get())
            config_loader.set("image_processing.enable_multithreading", self.enable_multithreading.get())
            config_loader.set("image_processing.max_workers", self.max_workers.get())

            # 設定を保存
            config_loader.save_config()

            # 後方互換性のためgui_settings.jsonも保存
            settings = {
                "docx_dir": self.docx_dir.get(),
                "images_dir": self.images_dir.get(),
                "html_dir": self.html_dir.get(),
                "output_dir": self.output_dir.get(),
                "webp_quality": self.webp_quality.get(),
                "enable_multithreading": self.enable_multithreading.get(),
                "max_workers": self.max_workers.get()
            }
            with open("gui_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

            # 一時的にステータスを表示（2秒後に元に戻す）
            if hasattr(self, 'progress_var') and self.progress_var is not None:
                original_text = self.progress_var.get()
                self.progress_var.set("設定を保存しました")
                self.root.after(2000, lambda: self.progress_var.set(original_text))

        except Exception as e:
            if hasattr(self, 'log_text') and self.log_text is not None:
                self._add_log(f"設定自動保存エラー: {e}", "error")
            else:
                print(f"設定自動保存エラー: {e}")

    def _update_multithread_display(self):
        """マルチスレッド設定表示を更新（リロード用）"""
        try:
            # 最新の設定を読み込み
            config_loader.reload_config()
            enabled = config_loader.get("image_processing.enable_multithreading", True)
            workers = config_loader.get("image_processing.max_workers", 4)

            # 変数を更新（イベントを発生させずに）
            self.enable_multithreading.set(enabled)
            self.max_workers.set(workers)

            # UI状態を更新
            self._on_multithread_toggle()

        except Exception as e:
            self._add_log(f"マルチスレッド設定読み込みエラー: {e}", "error")


def main():
    """GUIアプリケーションのメイン関数"""
    root = tk.Tk()

    # Windows用のスタイル設定
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except tk.TclError:
        # テーマファイルがない場合は標準スタイルを使用
        pass

    app = Img2WebpGUI(root)

    # アプリケーション終了時の処理
    def on_closing():
        if app.is_processing:
            if messagebox.askokcancel("確認", "処理中です。終了しますか？"):
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
