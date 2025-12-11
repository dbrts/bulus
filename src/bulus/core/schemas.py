import json
from typing import Any, Dict, List, Tuple, TypeAlias

from pydantic import BaseModel, Field, PrivateAttr, model_validator

from bulus.core.states import VALID_STATES_LIST

# --- Ice Structure ---
# (timestamp, tool_name, payload, state, storage, thought)
IceEntry: TypeAlias = Tuple[float, str, Dict[str, Any], str, Dict[str, Any], str | None]
IceHistory: TypeAlias = List[IceEntry]


# --- Action Model (SOTA for Strict Mode) ---
class Action(BaseModel):
    thought: str = Field(..., description="Internal reasoning: why am I taking this action?")
    tool_name: str = Field(..., description="Exact name of the tool to execute.")

    # Хак для Strict Mode: JSON внутри строки
    payload_str: str = Field(..., description="Tool arguments as a valid JSON string.")

    # Скрытое поле для внутреннего использования
    _payload: Dict[str, Any] = PrivateAttr(default_factory=dict)

    @property
    def payload(self) -> Dict[str, Any]:
        return self._payload

    @model_validator(mode="after")
    def validate_and_parse(self):
        # 1. Парсим JSON
        try:
            data = json.loads(self.payload_str)
        except json.JSONDecodeError:
            self._payload = {"error": "Invalid JSON string from LLM"}
            return self

        # 2. Валидация логики 'update'
        if self.tool_name == "update":
            if "state" in data:
                if data["state"] not in VALID_STATES_LIST:
                    data["error"] = f"Invalid state '{data['state']}'. Allowed: {VALID_STATES_LIST}"
                    del data["state"]

        self._payload = data
        return self
