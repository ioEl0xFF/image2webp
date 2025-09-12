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

# srcディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gui_processor import ProcessorThread
from src.config import WEBP_QUALITY, LOG_DIR
from src.config_loader import config_loader
from config_gui import ConfigEditorWindow


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
        main_frame.rowconfigure(6, weight=1)

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
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 5))

        progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_label.grid(row=5, column=0, columnspan=3, pady=(0, 10))

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
        ttk.Entry(file_frame, textvariable=self.docx_dir, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(file_frame, text="選択", command=lambda: self._select_directory(self.docx_dir)).grid(row=0, column=2)

        # 画像ディレクトリ
        ttk.Label(file_frame, text="画像ファイル:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.images_dir, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(file_frame, text="選択", command=lambda: self._select_directory(self.images_dir)).grid(row=1, column=2)

        # HTMLディレクトリ（オプション）
        ttk.Label(file_frame, text="HTMLファイル:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.html_dir, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(file_frame, text="選択", command=lambda: self._select_directory(self.html_dir)).grid(row=2, column=2)

        # 出力ディレクトリ
        ttk.Label(file_frame, text="出力先:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.output_dir, width=50).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(file_frame, text="選択", command=lambda: self._select_directory(self.output_dir)).grid(row=3, column=2)

    def _create_settings_section(self, parent):
        """設定セクションを作成"""
        settings_frame = ttk.LabelFrame(parent, text="変換設定", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # WebP品質設定
        ttk.Label(settings_frame, text="WebP品質:").grid(row=0, column=0, sticky=tk.W)
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

        ttk.Scale(quality_frame, from_=1, to=100, variable=self.webp_quality,
                 orient=tk.HORIZONTAL, length=200).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Label(quality_frame, textvariable=self.webp_quality).grid(row=0, column=1, padx=(10, 0))

        quality_frame.columnconfigure(0, weight=1)

    def _create_control_section(self, parent):
        """制御ボタンセクションを作成"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))

        self.start_button = ttk.Button(control_frame, text="変換開始",
                                      command=self._start_conversion, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, padx=(0, 10))

        self.stop_button = ttk.Button(control_frame, text="停止",
                                     command=self._stop_conversion, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))

        ttk.Button(control_frame, text="ログクリア",
                  command=self._clear_log).grid(row=0, column=2, padx=(0, 10))

        ttk.Button(control_frame, text="設定保存",
                  command=self._save_settings).grid(row=0, column=3, padx=(0, 10))
        
        ttk.Button(control_frame, text="詳細設定",
                  command=self._open_config_editor).grid(row=0, column=4)

    def _create_log_section(self, parent):
        """ログ表示セクションを作成"""
        log_frame = ttk.LabelFrame(parent, text="処理ログ", padding="5")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
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
        self.progress_bar.start(10)
        self.progress_var.set("処理中...")

        # ログクリア
        self._clear_log()
        # 全ログタブに切り替え
        self.log_notebook.select(0)
        self._add_log("=== 変換処理を開始します ===", "info")

        # 別スレッドで処理実行
        self.conversion_thread = threading.Thread(target=self._run_conversion)
        self.conversion_thread.daemon = True
        self.conversion_thread.start()

    def _stop_conversion(self):
        """変換処理停止"""
        if self.processor_thread and hasattr(self.processor_thread, 'cancel'):
            self._add_log("停止要求を受け付けました", "warning")
            self.processor_thread.cancel()

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
            'webp_quality': self.webp_quality.get()
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

    def _reset_ui_state(self):
        """UI状態をリセット"""
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_var.set("準備完了")

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

            # 重要なエラーの場合はエラータブに自動切り替え
            if level == "error":
                self.log_notebook.select(1)  # エラータブ（インデックス1）を選択

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
            else:
                # JSONコンフィグから読み込み
                self.docx_dir.set(str(current_dir / config_loader.get("directories.docx_directory", "docxs")))
                self.images_dir.set(str(current_dir / config_loader.get("directories.images_dir", "images")))
                self.html_dir.set(str(current_dir / config_loader.get("directories.html_dir", "html")))
                self.output_dir.set(str(current_dir / config_loader.get("directories.output_base_dir", "output")))
                self.webp_quality.set(config_loader.get("image_processing.webp_quality", WEBP_QUALITY))

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
            import src.config
            src.config.reload_config()
            
            # GUIの設定値も更新
            self._load_settings()
            
            self._add_log("設定画面を閉じました。設定を再読み込みしました", "info")
            
        except Exception as e:
            self._add_log(f"設定画面エラー: {e}", "error")




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
