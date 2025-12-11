import json

from bulus.core.states import VALID_STATES_LIST

# Описание инструментов
TOOLS_SCHEMA = {
    "send_message": "Send text to user. Args: {'text': str}",
    "update": """
    Update context. Atomic operation.
    Args (optional): 
    {
      'state': str,   # Transition to new FSM State
      'memory': dict  # Data to MERGE. Set value to null to delete.
    }
    """,
    "test_ping": "Execute ping logic. Args: {'payload': str}",
}


def get_system_prompt(state: str, storage: dict) -> str:
    return f"""
    You are the 'Stateless Brain' of Bulus.
    
    CONTEXT:
    - State: {state}
    - Memory: {json.dumps(storage, ensure_ascii=False)}
    
    CONSTRAINTS:
    - Valid States: {json.dumps(VALID_STATES_LIST)}
    - Tools: {json.dumps(TOOLS_SCHEMA)}
    
    STRATEGY:
    1. If user provides info -> Call `update` to save (memory) AND switch state.
    2. If state changed and you need to ask -> Call `send_message`.
    3. Output arguments as JSON STRING in 'payload_str'.
    4. If all fields (name, age, occupation) are known -> set state to 'call_ping'.
    5. If state is 'call_ping' -> call `test_ping` (any payload).
    
    Decide the SINGLE next action.
    """
