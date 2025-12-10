def apply_update(current_state: str, current_storage: dict, payload: dict):
    """
    Реализует логику PATCH для storage и смену стейта.
    """
    next_state = current_state
    next_storage = current_storage.copy()

    # 1. Смена стейта
    if "state" in payload and payload["state"]:
        next_state = payload["state"]

    # 2. Обновление памяти (Patch)
    if "memory" in payload and isinstance(payload["memory"], dict):
        for k, v in payload["memory"].items():
            if v is None:
                # Удаление ключа, если LLM прислала null
                if k in next_storage:
                    del next_storage[k]
            else:
                # Обновление / Добавление
                next_storage[k] = v

    return next_state, next_storage
