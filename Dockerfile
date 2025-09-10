FROM python:3.11-slim

WORKDIR /app

# 必要パッケージをインストール（cwebp 含む）
RUN apt-get update && apt-get install -y webp && apt-get clean

# 必要ライブラリを直接インストール
RUN pip install --no-cache-dir python-docx

# スクリプトをコピー
COPY main.py .

# デフォルトでスクリプトを実行
CMD ["python", "main.py"]
