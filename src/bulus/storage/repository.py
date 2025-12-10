import json
import os
from bulus.config import SESSIONS_DIR
from bulus.core.schemas import IceEntry, IceHistory


class BulusRepo:
    """Простое хранилище сессий в JSONL (Append-Only log)."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.file_path = os.path.join(SESSIONS_DIR, f"{session_id}.jsonl")

    def load_history(self) -> IceHistory:
        """Читает историю событий с диска."""
        if not os.path.exists(self.file_path):
            return []

        history = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        history.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass  # Пропускаем битые линии
        return history

    def append(self, entry: IceEntry):
        """Добавляет событие в конец файла."""
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
