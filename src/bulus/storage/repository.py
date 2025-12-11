import json
import os

from bulus.config import SESSIONS_DIR
from bulus.core.schemas import IceEntry


class BulusRepo:
    """Хранилище сессий с metadata и Ice history в одном JSON-файле."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")

    def _default_doc(self):
        return {"metadata": {"session_id": self.session_id, "status": "need_brain"}, "history": []}

    def _normalize_doc(self, data) -> dict:
        """Поддержка старого формата (список Ice) и нового с metadata."""
        if isinstance(data, list):
            return {"metadata": {"session_id": self.session_id, "status": "need_brain"}, "history": data}
        if not isinstance(data, dict):
            return self._default_doc()
        # Ensure required keys exist
        data.setdefault("metadata", {"session_id": self.session_id, "status": "need_brain"})
        data["metadata"].setdefault("session_id", self.session_id)
        data["metadata"].setdefault("status", "need_brain")
        data.setdefault("history", [])
        return data

    def load(self) -> dict:
        """Читает сессию (metadata + history) с диска."""
        if not os.path.exists(self.file_path):
            legacy_path = f"{self.file_path}l"  # .jsonl из старых версий
            if os.path.exists(legacy_path):
                ice = []
                with open(legacy_path, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                ice.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
                return self._normalize_doc(ice)
            return self._default_doc()
        with open(self.file_path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return self._default_doc()
        return self._normalize_doc(data)

    def save(self, doc: dict):
        """Перезаписывает сессию целиком."""
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)

    def append(self, entry: IceEntry, status: str | None = None):
        """Добавляет событие и при необходимости меняет статус."""
        doc = self.load()
        doc["history"].append(entry)
        if status:
            doc["metadata"]["status"] = status
        self.save(doc)

    def update_status(self, status: str):
        """Обновляет только статус сессии."""
        doc = self.load()
        doc["metadata"]["status"] = status
        self.save(doc)
