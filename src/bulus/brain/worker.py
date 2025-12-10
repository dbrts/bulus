from openai import OpenAI
from bulus.config import API_KEY, MODEL_NAME
from bulus.core.schemas import IceHistory, Action
from bulus.core.states import AgentState
from bulus.brain.prompts import get_system_prompt

client = OpenAI(api_key=API_KEY) if API_KEY else None


def stateless_brain(ice_history: IceHistory) -> Action:
    if not client:
        return Action(tool_name="error", payload_str="{}", thought="No API Key in .env")

    # 1. Восстановление контекста
    if not ice_history:
        current_state = AgentState.HELLO.value
        current_storage = {}
    else:
        last_ice = ice_history[-1]
        # (ts, tool, payload, state, storage, thought)
        current_state = last_ice[3] if len(last_ice) > 3 else "unknown"
        current_storage = last_ice[4] if len(last_ice) > 4 else {}

    # 2. Формирование Истории (Фильтруем старые мысли)
    items = []
    # Берем последние 15 записей для контекста
    recent_history = ice_history[-15:]

    for i, item in enumerate(recent_history):
        try:
            tool = item[1]
            payload = item[2]
            # thought = item[5] (пока скрываем для экономии)

            # Маппинг для LLM (читаемый вид)
            if tool == "user_said":
                items.append(f"[USER]: {payload}")
            elif tool == "send_message":
                items.append(f"[AGENT]: {payload.get('text', str(payload))}")
            elif tool == "update":
                changes = []
                if "state" in payload:
                    changes.append(f"State->{payload['state']}")
                if "memory" in payload:
                    changes.append("Memory Updated")
                items.append(f"[SYSTEM]: {', '.join(changes)}")
            elif tool == "test_ping":
                items.append("[SYSTEM]: Ping Executed")
        except:
            pass

    history_text = "\n".join(items)

    # 3. Вызов API
    try:
        completion = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": get_system_prompt(current_state, current_storage)},
                {"role": "user", "content": f"History:\n{history_text}\n\nNext step?"},
            ],
            response_format=Action,
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        return Action(tool_name="error", payload_str="{}", thought=f"LLM Error: {str(e)}")
