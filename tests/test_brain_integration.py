import os
import time

import pytest

from bulus.brain.worker import client, stateless_brain
from bulus.config import API_KEY
from bulus.core.states import AgentState
from bulus.runner.tools import apply_update

RUN_OPENAI = os.getenv("RUN_OPENAI_INTEGRATION") == "1"
PLACEHOLDER_KEYS = {"sk-proj-твой-ключ-здесь"}


def _require_real_client():
    if not RUN_OPENAI:
        pytest.skip("Set RUN_OPENAI_INTEGRATION=1 to run real OpenAI integration tests")
    if client is None:
        pytest.skip("OpenAI client is not configured (OPENAI_API_KEY missing)")
    if API_KEY in PLACEHOLDER_KEYS:
        pytest.skip("Replace placeholder OPENAI_API_KEY with a real key")


@pytest.mark.integration
def test_one_shot_reaches_call_ping_and_triggers_ping():
    _require_real_client()
    t0 = int(time.time())

    ice = [
        (t0 + 1, "send_message", {"text": "Привет! Представься для пинга."}, AgentState.HELLO.value, {}, "Init"),
        (
            t0 + 2,
            "user_said",
            "Привет! Меня зовут Алекс, мне 32 года, я работаю плотником.",
            AgentState.HELLO.value,
            {},
            None,
        ),
    ]

    act_oneshot = stateless_brain(ice)
    assert act_oneshot.tool_name == "update"

    payload = act_oneshot.payload
    assert payload.get("state") == AgentState.CALL_PING.value

    memory = payload.get("memory", {})
    assert memory.get("name")
    assert memory.get("occupation")
    assert str(memory.get("age", "")).strip()

    state_after, storage_after = apply_update(ice[-1][3], ice[-1][4], payload)
    ice_next = ice + [(t0 + 3, "update", payload, state_after, storage_after, act_oneshot.thought)]

    act_final = stateless_brain(ice_next)
    assert act_final.tool_name == "test_ping"
