# img2webp

📄 **DOCXファイルから画像名を抽出し、WebP形式に変換するPythonツール**

Word文書内のテーブルから画像名を自動抽出し、複数サイズのWebP画像を生成します。Webサイト用の画像最適化に最適です。

## ✨ 主な機能

- 🔍 **自動画像名抽出**: DOCXファイル内のテーブルから画像名を自動検出
- 🖼️ **複数サイズ変換**: 設定に基づいて複数のサイズでWebP画像を生成
- 📐 **アスペクト比保持**: 元画像の比率を維持しながらリサイズ
- 🔄 **メディアクエリベースHTML置換**: HTMLのメディアクエリに基づいて最適な画像サイズを自動選択
- 🎯 **レスポンシブ対応**: 画面サイズと解像度に応じた画像サイズの自動判定
- 🎠 **カーセル判定**: COMFRPTC12専用のカーセル/通常版判定機能
- 📊 **バッチ処理**: 複数のDOCXファイルを一括処理
- 📝 **詳細ログ**: 処理状況を詳細に記録
- 🏗️ **モジュラー設計**: 保守性とテスタビリティを重視した設計
- ⚠️ **高度なエラーハンドリング**: カスタム例外による詳細なエラー管理

## 🚀 クイックスタート

### 1. インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd img2webp

# 必要なパッケージをインストール
pip install python-docx Pillow
```

### 2. ファイル配置

```
img2webp/
├── docxs/          # 処理対象のDOCXファイル
├── images/         # 元画像ファイル（JPG/PNG/WebP）
├── html/           # 画像名置換対象のHTMLファイル（オプション）
├── src/            # Pythonソースコードディレクトリ
│   ├── __init__.py         # パッケージ初期化ファイル
│   ├── main.py             # メイン処理（統合クラス）
│   ├── exceptions.py       # カスタム例外クラス
│   ├── logger_utils.py     # ログユーティリティ
│   ├── html_processor.py   # HTML処理クラス
│   ├── file_manager.py     # ファイル管理クラス
│   ├── image_processor.py  # 画像処理クラス
│   ├── docx_parser.py      # DOCX解析クラス
│   ├── image_utils.py      # 画像処理ユーティリティ
│   └── config.py           # 設定ファイル
├── main.py         # メインエントリーポイント
└── README.md       # プロジェクト説明書
```

### 3. 実行

```bash
python main.py
```

## 📋 使用方法

### DOCXファイルの形式

テーブル内で以下の形式で画像名を記述してください：

| コード | 画像名 |
|--------|--------|
| COMFRPTC09 | ＜画像＞image-name-01 |
| GSTFRPTA15 | ＜画像名＞image-name-02 |

**対応パターン:**
- `＜画像＞image-name-01`
- `＜画像名＞image-name-02`
- `＜画像1＞image-name-03`
- `＜画像（補足）＞image-name-04`
- `画像名：image-name-05` (全角コロン)
- `画像名:image-name-06` (半角コロン)

### 設定カスタマイズ

`config.py`で以下の設定を変更できます：

```python
# 画像サイズ設定
WIDTH_MAP = {
    "COMFRPTC09": [[1800, 1200], [1200, 800], [900, 600], [500, 333]],
    "COMFRPTC12": [[1800, 1200], [1200, 800], [900, 600], [500, 333]],
    "GSTFRPTA15": [[900, 0], [500, 0]],  # 高さ0はアスペクト比保持
}

# メディアクエリベースのサイズマッピング
MIN_WIDTH_SIZE_MAP = {
    "COMFRPTC12": {
        1562: [1800, 900],  # 複数サイズ対応（カーセル/通常版）
        1041: [1200, 900],  # 複数サイズ対応（カーセル/通常版）
        781: 900,
        768: 500,
        "source_default": 900,
        "img_default": 500
    }
}

# WebP品質設定
WEBP_QUALITY = 100
```

## 📁 出力構造

```
output/
├── ファイル名1/
│   ├── image-name-011800.webp
│   ├── image-name-011200.webp
│   └── image-name-01900.webp
└── ファイル名2/
    └── image-name-021800.webp
```

## 🔄 HTML画像名置換機能

### 動作概要

1. **自動検索**: `html/`ディレクトリでDOCXファイル名と同じHTMLファイルを検索
2. **画像名抽出**: DOCXから抽出した画像名情報を取得
3. **メディアクエリ解析**: HTMLの`<source>`タグのメディアクエリを解析
4. **レスポンシブ対応**: 画面サイズと解像度に応じて最適な画像サイズを選択
5. **自動置換**: HTML内の画像ファイル名をWebP形式に置換
6. **ファイル更新**: 置換後のHTMLファイルを保存

### メディアクエリベース置換

**対応コード**: COMFRPTC12, COMFRPTC09, COMFRPTC14, COMFRPTC13, COMFRPTC34, COMFRPTC15, COMFRPTC23, COMFRPTC17, COMFRPTC21, GSTFRPTA15, COMFRPTC03, COMFRPTC30, THUMBNAIL

**置換例:**

**置換前:**
```html
<source media="(min-width: 1562px) and (min-resolution: 2dppx)"
        data-srcset="sample-image-01.jpg">
<img data-src="sample-image-01.jpg" alt="サンプル画像">
```

**置換後（COMFRPTC12設定の場合）:**
```html
<source media="(min-width: 1562px) and (min-resolution: 2dppx)"
        data-srcset="sample-image-011800.webp">  <!-- カーセル版の場合 -->
<img data-src="sample-image-01500.webp" alt="サンプル画像">
```

### カーセル判定機能（COMFRPTC12専用）

COMFRPTC12では、カーセル版と通常版で異なる画像サイズを使用します：

- **カーセル版**: 大きいサイズ（1800px, 1200px）
- **通常版**: 小さいサイズ（900px）

**判定ロジック:**
1. 画像タグの位置から上方向に最大50行まで探索
2. `_carousel`が見つかった場合 → カーセル版
3. `mCommonsectionImgitem`が見つかった場合 → 通常版
4. 50行探しても見つからない場合 → 通常版

## 🛠️ トラブルシューティング

### よくある問題と解決方法

| 問題 | 解決方法 |
|------|----------|
| 画像ファイルが見つからない | `images/`ディレクトリにファイルが存在するか確認 |
| DOCXファイルが読み込めない | ファイルが破損していないか確認 |
| 変換に失敗する | 画像ファイルが破損していないか、対応形式か確認 |
| 再変換したい | `output/`内の対象フォルダを削除してから再実行 |
| HTML置換が動作しない | HTMLファイル名がDOCXファイル名と一致しているか確認 |
| メディアクエリベース置換が動作しない | コードがMIN_WIDTH_SIZE_MAPに定義されているか確認 |
| カーセル判定が正しく動作しない | HTML内に`_carousel`または`mCommonsectionImgitem`が含まれているか確認 |
| エラーの詳細を確認したい | `.logs/LOG.log`ファイルで詳細なエラーログを確認 |
| 存在しない画像を確認したい | `.logs/missing_images.txt`で存在しない画像一覧を確認 |
| モジュールインポートエラー | 必要なパッケージ（python-docx, Pillow）がインストールされているか確認 |

## 📊 対応形式

### 入力形式
- JPG/JPEG
- PNG
- WebP

### 出力形式
- WebP（複数サイズ）

## 🏗️ アーキテクチャ

### モジュラー設計

リファクタリングにより、以下のクラスベース設計を採用しています：

- **`Img2WebpProcessor`**: メイン処理を統合する中央クラス
- **`DocxAnalyzer`**: DOCX解析を担当
- **`ImageProcessor`**: 画像変換処理を担当
- **`HtmlProcessor`**: HTML画像名置換を担当
- **`FileManager`**: ファイル操作を担当

### エラーハンドリング

カスタム例外クラスによる詳細なエラー管理：

- **`Img2WebpError`**: 基底例外クラス
- **`DocxFileError`**: DOCXファイル関連エラー
- **`ImageFileError`**: 画像ファイル関連エラー
- **`ImageConversionError`**: 画像変換エラー
- **`HtmlProcessingError`**: HTML処理エラー
- **`ConfigurationError`**: 設定関連エラー

## 📝 ログ機能

処理の詳細情報は以下のファイルに保存されます：

- `.logs/LOG.log`: 詳細な処理ログ
- `.logs/all_image_names.json`: 全ファイルの画像名情報
- `.logs/all_converted_images.txt`: 変換済み画像ファイル一覧
- `.logs/missing_images.txt`: 存在しない画像ファイル一覧

## 🔧 必要な環境

- **Python**: 3.7以上
- **パッケージ**:
  - `python-docx`: DOCXファイル読み込み
  - `Pillow`: 画像処理

## 📈 更新履歴

- **v1.0**: 初期バージョン（DOCX解析とWebP変換）
- **v1.1**: ログ機能追加
- **v1.2**: 複数サイズ対応
- **v1.3**: アスペクト比保持機能
- **v1.4**: HTML画像名置換機能追加
- **v1.5**: メディアクエリベースHTML置換機能追加
- **v1.6**: 画像名パターン拡張（半角コロン対応）
- **v1.7**: COMFRPTC12専用カーセル判定機能追加
- **v1.8**: 従来の順次置換処理を削除、メディアクエリベース処理に統一
- **v2.0**: 🎉 **大規模リファクタリング**
  - モジュラー設計への移行（クラスベース）
  - カスタム例外クラスの導入
  - エラーハンドリングの強化
  - コード品質の大幅改善（main.py 614行 → 160行）
  - 保守性・テスタビリティの向上

## 🤝 貢献

バグ報告や機能改善の提案は、IssueまたはPull Requestでお願いします。

## 📄 ライセンス

このプロジェクトのライセンスについては、プロジェクトのライセンスファイルを参照してください。