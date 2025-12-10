import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Загрузка переменных окружения
# Ищем .env в корне проекта (на 3 уровня выше этого файла)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# 2. Ключи и Модели
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-5-mini"  # Или gpt-4o-mini

# 3. Настройки хранилища
BULUS_DIR = BASE_DIR / ".bulus"
BLOBS_DIR = BULUS_DIR / "blobs"
SESSIONS_DIR = BULUS_DIR / "sessions"

# Авто-создание папок
os.makedirs(BLOBS_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)
