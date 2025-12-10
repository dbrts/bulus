"""
Simple runnable scenarios against the real OpenAI-backed brain.

Usage:
  python scripts/run_scenarios.py

Requires:
  - OPENAI_API_KEY in .env or environment
  - Optional: OPENAI_MODEL_NAME (defaults to gpt-5-mini)
"""

import sys
import time
from pathlib import Path

# Ensure src/ is importable when running as a script
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bulus.brain.worker import stateless_brain, client  # type: ignore  # noqa: E402
from bulus.config import API_KEY, MODEL_NAME  # type: ignore  # noqa: E402
from bulus.core.states import AgentState  # type: ignore  # noqa: E402
from bulus.runner.tools import apply_update  # type: ignore  # noqa: E402


PLACEHOLDER_KEYS = {"sk-proj-твой-ключ-здесь"}


def _check_client():
    if API_KEY is None or API_KEY in PLACEHOLDER_KEYS or not API_KEY.strip():
        raise SystemExit("ERROR: Set a real OPENAI_API_KEY in .env to run scenarios.")
    if client is None:
        raise SystemExit("ERROR: OpenAI client is not initialized.")


def _print_action(tag: str, action):
    print(f"--- {tag} ---")
    print(f"Thought: {action.thought}")
    print(f"Tool:    {action.tool_name}")
    print(f"Payload: {action.payload}")


def run_multi_turn():
    print(f"🧠 [MULTI-TURN] Using model {MODEL_NAME}...")
    t0 = int(time.time())

    history_turn_1 = [
        (t0 + 1, "send_message", {"text": "Как тебя зовут?"}, AgentState.ASK_NAME.value, {}, "Start"),
        (t0 + 2, "user_said", "Меня зовут Семен", AgentState.ASK_NAME.value, {}, None),
    ]

    act1 = stateless_brain(history_turn_1)
    _print_action("RESULT 1", act1)
    assert act1.tool_name == "update", "Expected update after receiving name"
    assert act1.payload.get("state") == AgentState.ASK_AGE.value
    assert act1.payload.get("memory", {}).get("name")

    next_state, next_storage = apply_update(history_turn_1[-1][3], history_turn_1[-1][4], act1.payload)
    history_turn_2 = history_turn_1 + [(t0 + 3, act1.tool_name, act1.payload, next_state, next_storage, act1.thought)]

    history_turn_2.extend(
        [
            (t0 + 4, "send_message", {"text": "Приятно познакомиться, Семен! Сколько тебе лет?"}, next_state, next_storage, "Ask age"),
            (t0 + 5, "user_said", "Мне сейчас 25", next_state, next_storage, None),
        ]
    )

    act2 = stateless_brain(history_turn_2)
    _print_action("RESULT 2", act2)
    assert act2.tool_name == "update", "Expected update after receiving age"
    assert act2.payload.get("state") == AgentState.ASK_OCCUPATION.value
    assert act2.payload.get("memory", {}).get("age")

    next_state2, next_storage2 = apply_update(history_turn_2[-1][3], history_turn_2[-1][4], act2.payload)
    history_turn_3 = history_turn_2 + [(t0 + 6, act2.tool_name, act2.payload, next_state2, next_storage2, act2.thought)]

    history_turn_3.extend(
        [
            (t0 + 7, "send_message", {"text": "Супер, 25 — отличный возраст! А кем работаешь?"}, next_state2, next_storage2, "Ask job"),
            (t0 + 8, "user_said", "Я работаю AI инженером", next_state2, next_storage2, None),
        ]
    )

    act3 = stateless_brain(history_turn_3)
    _print_action("RESULT 3", act3)
    assert act3.tool_name == "update", "Expected update after receiving occupation"
    assert act3.payload.get("state") == AgentState.CALL_PING.value
    assert act3.payload.get("memory", {}).get("occupation")

    print("✅ Multi-turn scenario passed.\n")


def run_one_shot():
    print(f"🚀 [ONE-SHOT] Using model {MODEL_NAME}...")
    t0 = int(time.time())

    history = [
        (t0 + 1, "send_message", {"text": "Привет! Представься для пинга."}, AgentState.HELLO.value, {}, "Init"),
        (t0 + 2, "user_said", "Привет! Меня зовут Алекс, мне 32 года, я работаю плотником.", AgentState.HELLO.value, {}, None),
    ]

    act = stateless_brain(history)
    _print_action("RESULT (ONE-SHOT)", act)
    assert act.tool_name == "update", "Expected update after receiving full profile"
    assert act.payload.get("state") == AgentState.CALL_PING.value
    memory = act.payload.get("memory", {})
    assert memory.get("name")
    assert memory.get("age")
    assert memory.get("occupation")

    next_state, next_storage = apply_update(history[-1][3], history[-1][4], act.payload)
    history_next = history + [(t0 + 3, "update", act.payload, next_state, next_storage, act.thought)]

    act_next = stateless_brain(history_next)
    _print_action("RESULT (CALL PING)", act_next)
    assert act_next.tool_name == "test_ping", "Expected test_ping after reaching call_ping"

    print("✅ One-shot scenario passed.\n")


def main():
    _check_client()
    run_multi_turn()
    run_one_shot()
    print("🎉 All scenario checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
