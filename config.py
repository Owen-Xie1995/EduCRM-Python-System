"""從環境變數或專案目錄的 .env 讀取連線設定。"""
import os
from pathlib import Path

from dotenv import load_dotenv


def database_config():
    load_dotenv(Path(__file__).with_name('.env'))
    user = os.getenv('DB_USER', '').strip()
    password = os.getenv('DB_PASSWORD', '')
    if not user or not password:
        raise ValueError('請在 .env 設定 DB_USER 與非空的 DB_PASSWORD；範例見 .env.example')
    try:
        port = int(os.getenv('DB_PORT', '3306'))
    except ValueError as exc:
        raise ValueError('DB_PORT 必須是整數') from exc
    if not 1 <= port <= 65535:
        raise ValueError('DB_PORT 必須介於 1 與 65535')
    return {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': port,
        'user': user,
        'password': password,
        'database': os.getenv('DB_NAME', 'student_db'),
    }
