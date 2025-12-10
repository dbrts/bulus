from enum import Enum


class AgentState(str, Enum):
    HELLO = "hello"
    ASK_NAME = "ask_name"
    ASK_AGE = "ask_age"
    ASK_OCCUPATION = "ask_occupation"
    CALL_PING = "call_ping"


# Список для валидации в Pydantic
VALID_STATES_LIST = [s.value for s in AgentState]
