import time
from bulus.core.schemas import IceHistory, IceEntry, Action
from bulus.core.states import AgentState
from bulus.runner.tools import apply_update


def imperative_runner(ice_history: IceHistory, action: Action) -> IceEntry:
    """
    Исполняет Action, мутирует данные и возвращает НОВЫЙ IceEntry.
    """
    # 1. Инит контекста из последнего кадра
    if not ice_history:
        current_state = AgentState.HELLO.value
        current_storage = {}
    else:
        last_ice = ice_history[-1]
        current_state = last_ice[3]
        current_storage = last_ice[4]

    tool = action.tool_name
    payload = action.payload
    thought = action.thought

    # Будущий контекст (по дефолту не меняется)
    next_state = current_state
    next_storage = current_storage

    # 2. Роутинг
    if tool == "update":
        next_state, next_storage = apply_update(current_state, current_storage, payload)

    elif tool == "send_message":
        print(f" >>> [REAL MESSAGE SENT]: {payload.get('text')}")

    elif tool == "test_ping":
        print(" >>> PONG! 🏓 (Backend service triggered)")

    elif tool == "error":
        print(f" >>> [ERROR]: {thought}")

    # 3. Сборка нового Ice
    new_entry = (
        time.time(),
        tool,
        payload,
        next_state,
        next_storage,
        thought,
    )

    return new_entry
