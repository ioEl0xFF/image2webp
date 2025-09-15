"""
GUI共通コンポーネント
再利用可能なUIコンポーネントを提供
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Optional, Any
from pathlib import Path


class DirectorySelector(ttk.Frame):
    """ディレクトリ選択コンポーネント"""
    
    def __init__(self, parent, label_text: str, initial_path: str = "", 
                 on_change: Optional[Callable[[str], None]] = None):
        super().__init__(parent)
        
        self._on_change = on_change
        self.path_var = tk.StringVar(value=initial_path)
        self.path_var.trace('w', self._on_path_changed)
        
        # ラベル
        label = ttk.Label(self, text=label_text)
        label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # パス表示エントリ
        self.path_entry = ttk.Entry(self, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # 参照ボタン
        browse_btn = ttk.Button(self, text="参照", command=self._browse_directory)
        browse_btn.grid(row=0, column=2)
        
        # グリッドの重み設定
        self.columnconfigure(1, weight=1)
    
    def _browse_directory(self):
        """ディレクトリ選択ダイアログを表示"""
        current_path = self.path_var.get()
        initial_dir = current_path if Path(current_path).exists() else Path.cwd()
        
        selected_dir = filedialog.askdirectory(
            title=f"ディレクトリを選択",
            initialdir=initial_dir
        )
        
        if selected_dir:
            self.path_var.set(selected_dir)
    
    def _on_path_changed(self, *args):
        """パス変更時のコールバック"""
        if self._on_change:
            self._on_change(self.path_var.get())
    
    def get_path(self) -> str:
        """現在のパスを取得"""
        return self.path_var.get()
    
    def set_path(self, path: str):
        """パスを設定"""
        self.path_var.set(path)


class ProgressDisplay(ttk.Frame):
    """進捗表示コンポーネント"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # 進捗バー
        self.progress_bar = ttk.Progressbar(self, mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # ステータステキスト
        self.status_var = tk.StringVar(value="準備完了")
        status_label = ttk.Label(self, textvariable=self.status_var)
        status_label.grid(row=1, column=0)
        
        # グリッドの重み設定
        self.columnconfigure(0, weight=1)
    
    def start_progress(self, message: str = "処理中..."):
        """進捗表示を開始"""
        self.status_var.set(message)
        self.progress_bar.start(10)  # 10ms間隔でアニメーション
    
    def stop_progress(self, message: str = "完了"):
        """進捗表示を停止"""
        self.progress_bar.stop()
        self.status_var.set(message)
    
    def update_status(self, message: str):
        """ステータスメッセージを更新"""
        self.status_var.set(message)


class LogDisplay(ttk.Frame):
    """ログ表示コンポーネント"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # ラベル
        log_label = ttk.Label(self, text="処理ログ")
        log_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # ログテキストエリア（スクロール付き）
        self.log_text = tk.Text(self, height=15, wrap=tk.WORD, 
                               font=('Consolas', 9), state=tk.DISABLED)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # グリッド配置
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # クリアボタン
        clear_btn = ttk.Button(self, text="ログクリア", command=self.clear_log)
        clear_btn.grid(row=2, column=0, pady=(5, 0), sticky=tk.W)
        
        # グリッドの重み設定
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
    
    def append_log(self, message: str, level: str = "INFO"):
        """ログメッセージを追加"""
        self.log_text.configure(state=tk.NORMAL)
        
        # レベルに応じた色分け
        tag_name = f"level_{level}"
        if level == "ERROR":
            self.log_text.tag_configure(tag_name, foreground="red")
        elif level == "WARNING":
            self.log_text.tag_configure(tag_name, foreground="orange")
        elif level == "SUCCESS":
            self.log_text.tag_configure(tag_name, foreground="green")
        else:
            self.log_text.tag_configure(tag_name, foreground="black")
        
        # メッセージを追加
        self.log_text.insert(tk.END, f"{message}\n", tag_name)
        self.log_text.see(tk.END)  # 最新のメッセージにスクロール
        
        self.log_text.configure(state=tk.DISABLED)
        self.update_idletasks()  # UIを即座に更新
    
    def clear_log(self):
        """ログをクリア"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)


class SettingsPanel(ttk.LabelFrame):
    """設定パネルコンポーネント"""
    
    def __init__(self, parent, title: str = "設定"):
        super().__init__(parent, text=title, padding="10")
        
        self.settings = {}
        self.row_count = 0
    
    def add_spinbox_setting(self, key: str, label: str, 
                           initial_value: int, min_value: int, max_value: int,
                           on_change: Optional[Callable[[int], None]] = None):
        """スピンボックス設定項目を追加"""
        # ラベル
        label_widget = ttk.Label(self, text=label)
        label_widget.grid(row=self.row_count, column=0, sticky=tk.W, padx=(0, 10))
        
        # スピンボックス
        var = tk.IntVar(value=initial_value)
        spinbox = ttk.Spinbox(self, from_=min_value, to=max_value, 
                             textvariable=var, width=10)
        spinbox.grid(row=self.row_count, column=1, sticky=tk.W)
        
        # コールバック設定
        if on_change:
            var.trace('w', lambda *args: on_change(var.get()))
        
        self.settings[key] = var
        self.row_count += 1
    
    def add_checkbox_setting(self, key: str, label: str, 
                           initial_value: bool,
                           on_change: Optional[Callable[[bool], None]] = None):
        """チェックボックス設定項目を追加"""
        var = tk.BooleanVar(value=initial_value)
        checkbox = ttk.Checkbutton(self, text=label, variable=var)
        checkbox.grid(row=self.row_count, column=0, columnspan=2, sticky=tk.W)
        
        # コールバック設定
        if on_change:
            var.trace('w', lambda *args: on_change(var.get()))
        
        self.settings[key] = var
        self.row_count += 1
    
    def get_setting(self, key: str) -> Any:
        """設定値を取得"""
        if key in self.settings:
            return self.settings[key].get()
        return None
    
    def set_setting(self, key: str, value: Any):
        """設定値を設定"""
        if key in self.settings:
            self.settings[key].set(value)


class ButtonPanel(ttk.Frame):
    """ボタンパネルコンポーネント"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.buttons = {}
        self.column_count = 0
    
    def add_button(self, key: str, text: str, command: Callable[[], None],
                  style: str = ""):
        """ボタンを追加"""
        if style:
            button = ttk.Button(self, text=text, command=command, style=style)
        else:
            button = ttk.Button(self, text=text, command=command)
        
        button.grid(row=0, column=self.column_count, padx=(0, 10))
        self.buttons[key] = button
        self.column_count += 1
    
    def enable_button(self, key: str):
        """ボタンを有効化"""
        if key in self.buttons:
            self.buttons[key].configure(state=tk.NORMAL)
    
    def disable_button(self, key: str):
        """ボタンを無効化"""
        if key in self.buttons:
            self.buttons[key].configure(state=tk.DISABLED)
    
    def get_button(self, key: str) -> Optional[ttk.Button]:
        """ボタンウィジェットを取得"""
        return self.buttons.get(key)
