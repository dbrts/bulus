"""
Lightweight simulation of the Bulus blackboard:
- Sessions (Ice) live in .bulus/sessions as JSON: {"metadata": {"status": ...}, "history": [...]}
- Brain workers pick sessions with status=need_brain, craft an Action, and stash it as pending_action -> need_runner.
- Runner workers pick status=need_runner, apply the pending Action via imperative_runner, and set status to still/need_brain/done.
- A tiny "user" loop feeds canned replies when status=still to unblock the next brain step.

Run:
    python scripts/simulate_bulus.py

No real OpenAI calls are made; we use a deterministic fake brain.
"""

import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Iterable

# Ensure src/ is importable when running as a script
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bulus.core.schemas import Action
from bulus.core.states import AgentState
from bulus.runner.worker import imperative_runner
from bulus.storage import repository as repo_mod
from bulus.storage.repository import BulusRepo

# States that imply we're waiting for user input after runner applies an update
WAITING_STATES = {
    AgentState.ASK_NAME.value,
    AgentState.ASK_AGE.value,
    AgentState.ASK_OCCUPATION.value,
}

# Canned user replies for the demo
USER_REPLIES = {
    AgentState.ASK_NAME.value: "Я тестовый пользователь",
    AgentState.ASK_AGE.value: "Мне 25",
    AgentState.ASK_OCCUPATION.value: "Я инженер",
}


def _make_action(tool_name: str, payload: Dict[str, Any], thought: str) -> Action:
    return Action(tool_name=tool_name, payload_str=json.dumps(payload, ensure_ascii=False), thought=thought)


def fake_brain(history: list) -> Action:
    """Deterministic brain: fills name -> age -> occupation -> test_ping."""
    state = history[-1][3] if history else AgentState.HELLO.value
    storage = history[-1][4] if history else {}

    if "name" not in storage:
        return _make_action(
            "update",
            {"state": AgentState.ASK_AGE.value, "memory": {"name": "Demo User"}},
            "Добавить имя и перейти к возрасту",
        )
    if "age" not in storage:
        return _make_action(
            "update",
            {"state": AgentState.ASK_OCCUPATION.value, "memory": {"age": 30}},
            "Добавить возраст и спросить профессию",
        )
    if "occupation" not in storage:
        return _make_action(
            "update",
            {"state": AgentState.CALL_PING.value, "memory": {"occupation": "engineer"}},
            "Добавить профессию и перейти к ping",
        )

    return _make_action("test_ping", {"payload": "ping"}, "Все данные есть — пингуем")


def _iter_repos(sessions_dir: Path) -> Iterable[BulusRepo]:
    for path in sorted(sessions_dir.glob("*.json")):
        yield BulusRepo(path.stem)


def seed_sessions(sessions_dir: Path):
    """Create two demo sessions with different starting points."""
    now = time.time()
    sessions = {
        "sim_alpha": [],  # пустая история
        "sim_bravo": [
            (now, "user_said", "Привет, я Браво!", AgentState.HELLO.value, {}, None),
        ],
    }
    for sid, history in sessions.items():
        repo = BulusRepo(sid)
        repo.save({"metadata": {"session_id": sid, "status": "need_brain"}, "history": history})


def brain_worker(sessions_dir: Path):
    for repo in _iter_repos(sessions_dir):
        doc = repo.load()
        meta = doc["metadata"]
        if meta.get("status") != "need_brain":
            continue
        action = fake_brain(doc["history"])
        meta["pending_action"] = {
            "tool_name": action.tool_name,
            "payload": action.payload,
            "thought": action.thought,
        }
        meta["status"] = "need_runner"
        repo.save(doc)
        print(f"[brain] {repo.session_id}: {action.tool_name} -> status need_runner")


def runner_worker(sessions_dir: Path):
    for repo in _iter_repos(sessions_dir):
        doc = repo.load()
        meta = doc["metadata"]
        if meta.get("status") != "need_runner":
            continue
        pending = meta.get("pending_action")
        if not pending:
            continue
        action = _make_action(pending["tool_name"], pending.get("payload", {}), pending.get("thought", ""))
        new_entry = imperative_runner(doc["history"], action)
        doc["history"].append(new_entry)

        next_state = new_entry[3]
        if action.tool_name == "test_ping":
            next_status = "done"
        elif next_state in WAITING_STATES:
            next_status = "still"
        else:
            next_status = "need_brain"

        meta["pending_action"] = None
        meta["status"] = next_status
        repo.save(doc)
        print(f"[runner] {repo.session_id}: applied {action.tool_name} -> status {next_status}")


def user_worker(sessions_dir: Path):
    for repo in _iter_repos(sessions_dir):
        doc = repo.load()
        meta = doc["metadata"]
        if meta.get("status") != "still":
            continue
        if not doc["history"]:
            continue
        state = doc["history"][-1][3]
        storage = doc["history"][-1][4]
        reply = USER_REPLIES.get(state)
        if not reply:
            continue
        user_entry = (time.time(), "user_said", reply, state, storage, None)
        doc["history"].append(user_entry)
        meta["status"] = "need_brain"
        repo.save(doc)
        print(f"[user] {repo.session_id}: replied for state {state} -> status need_brain")


def print_summary(sessions_dir: Path):
    rows = []
    for repo in _iter_repos(sessions_dir):
        doc = repo.load()
        state = doc["history"][-1][3] if doc["history"] else "n/a"
        storage = doc["history"][-1][4] if doc["history"] else {}
        rows.append((repo.session_id, doc["metadata"]["status"], state, storage))

    print("\n=== BULUS SNAPSHOT ===")
    for sid, status, state, storage in rows:
        print(f"{sid:10s} | status={status:11s} | state={state:15s} | storage={storage}")
    print("======================\n")


def main(cycles: int = 5):
    with tempfile.TemporaryDirectory(prefix="bulus_sim_") as tmp:
        sessions_dir = Path(tmp) / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        # Redirect BulusRepo to the temp sandbox
        repo_mod.SESSIONS_DIR = str(sessions_dir)

        seed_sessions(sessions_dir)
        print(f"Using temp sessions dir: {sessions_dir}\n")

        for step in range(cycles):
            print(f"--- cycle {step + 1} ---")
            brain_worker(sessions_dir)
            runner_worker(sessions_dir)
            user_worker(sessions_dir)
            print_summary(sessions_dir)
            time.sleep(0.2)


if __name__ == "__main__":
    main()
