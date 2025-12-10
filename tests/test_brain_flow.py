import json
from typing import List

from bulus.brain import worker as brain_worker
from bulus.core.schemas import Action
from bulus.core.states import AgentState
from bulus.runner.tools import apply_update


def make_action(tool_name: str, payload: dict, thought: str) -> Action:
    return Action(tool_name=tool_name, payload_str=json.dumps(payload, ensure_ascii=False), thought=thought)


class _FakeResponse:
    def __init__(self, action: Action):
        self.choices = [type("Choice", (), {"message": type("Msg", (), {"parsed": action})()})()]


class _FakeCompletions:
    def __init__(self, actions_queue: List[Action]):
        self._queue = list(actions_queue)

    def parse(self, **kwargs):
        if not self._queue:
            raise AssertionError("No actions left in fake completions queue")
        action = self._queue.pop(0)
        return _FakeResponse(action)


class _FakeClient:
    def __init__(self, actions_queue: List[Action]):
        self.beta = type("Beta", (), {"chat": type("Chat", (), {"completions": _FakeCompletions(actions_queue)})()})()


def test_multi_turn_brain_flow(monkeypatch):
    t0 = 1715000000
    fake_actions = [
        make_action("update", {"state": "ask_age", "memory": {"name": "Семен"}}, "Got name, moving to age"),
        make_action("update", {"state": "ask_occupation", "memory": {"age": 25}}, "Got age, moving to occupation"),
        make_action("update", {"state": "call_ping", "memory": {"occupation": "AI инженер"}}, "Got occupation, ready to ping"),
    ]
    monkeypatch.setattr(brain_worker, "client", _FakeClient(fake_actions))

    history = [
        (t0 + 1, "send_message", {"text": "Как тебя зовут?"}, AgentState.ASK_NAME.value, {}, "Start"),
        (t0 + 2, "user_said", "Меня зовут Семен", AgentState.ASK_NAME.value, {}, None),
    ]

    act1 = brain_worker.stateless_brain(history)
    assert act1.tool_name == "update"
    assert act1.payload["memory"] == {"name": "Семен"}

    state1, storage1 = apply_update(history[-1][3], history[-1][4], act1.payload)
    history.append((t0 + 3, act1.tool_name, act1.payload, state1, storage1, act1.thought))

    history.extend(
        [
            (t0 + 4, "send_message", {"text": "Приятно познакомиться, Семен! Сколько тебе лет?"}, state1, storage1, "Ask age"),
            (t0 + 5, "user_said", "Мне сейчас 25", state1, storage1, None),
        ]
    )

    act2 = brain_worker.stateless_brain(history)
    assert act2.tool_name == "update"
    assert act2.payload["state"] == "ask_occupation"
    assert act2.payload["memory"] == {"age": 25}

    state2, storage2 = apply_update(history[-1][3], history[-1][4], act2.payload)
    history.append((t0 + 6, act2.tool_name, act2.payload, state2, storage2, act2.thought))

    history.extend(
        [
            (t0 + 7, "send_message", {"text": "Супер, 25 — отличный возраст! А кем работаешь?"}, state2, storage2, "Ask job"),
            (t0 + 8, "user_said", "Я работаю AI инженером", state2, storage2, None),
        ]
    )

    act3 = brain_worker.stateless_brain(history)
    assert act3.tool_name == "update"
    assert act3.payload["state"] == "call_ping"
    assert act3.payload["memory"] == {"occupation": "AI инженер"}


def test_one_shot_and_next_step(monkeypatch):
    t0 = 1715000000
    fake_actions = [
        make_action(
            "update",
            {"state": "call_ping", "memory": {"name": "Алекс", "age": 32, "occupation": "плотник"}},
            "All info provided",
        ),
        make_action("test_ping", {"payload": "ping"}, "Trigger ping"),
    ]
    monkeypatch.setattr(brain_worker, "client", _FakeClient(fake_actions))

    history = [
        (t0 + 1, "send_message", {"text": "Привет! Представься для пинга."}, AgentState.HELLO.value, {}, "Init"),
        (t0 + 2, "user_said", "Привет! Меня зовут Алекс, мне 32 года, я работаю плотником.", AgentState.HELLO.value, {}, None),
    ]

    act_oneshot = brain_worker.stateless_brain(history)
    assert act_oneshot.tool_name == "update"
    assert act_oneshot.payload["state"] == "call_ping"
    assert act_oneshot.payload["memory"] == {"name": "Алекс", "age": 32, "occupation": "плотник"}

    state_after, storage_after = apply_update(history[-1][3], history[-1][4], act_oneshot.payload)
    history_next = history + [(t0 + 3, "update", act_oneshot.payload, state_after, storage_after, act_oneshot.thought)]

    act_final = brain_worker.stateless_brain(history_next)
    assert act_final.tool_name == "test_ping"
