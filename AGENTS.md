# Repository Guidelines

## Project Structure & Module Organization
- Core code lives in `src/bulus`: `brain/` holds the stateless brain and prompts, `core/` defines schemas (e.g., `IceEntry`, `Action`, `AgentState`), `runner/` executes tools like `apply_update`, and `engine/` contains the loop orchestration. `config.py` loads `.env` and prepares `.bulus/` storage directories (`blobs/`, `sessions/`).
- Supporting assets: `viewer/` contains the time-travel HTML viewer, `dist/` ships built artifacts, and `.bulus/` is generated runtime state (keep it out of commits).
- Tests live in `tests/` with unit flows and OpenAI integration coverage; scripts for manual runs sit in `scripts/` (see `run_scenarios.py`).

## Build, Test, and Development Commands
- Install: `pip install -e .` (or `pip install -r requirements.txt`) after activating your virtualenv. Requires Python 3.8+.
- Fast tests: `pytest` (default unit suite; no network).
- Integration: `RUN_OPENAI_INTEGRATION=1 OPENAI_API_KEY=... pytest -m integration` hits the real API; skips automatically if the key is missing or placeholder.
- Manual scenario check with the live LLM: `OPENAI_API_KEY=... python scripts/run_scenarios.py` (validates multi-turn and one-shot flows against `AgentState` transitions).

## Coding Style & Naming Conventions
- Use 4-space indentation, type hints, and keep functions side-effect-light; the brain is deterministic given history.
- Preserve the Ice tuple shape `(timestamp, tool_name, payload, state, storage, thought)`; avoid mutating storage outside `apply_update`.
- Models rely on Pydantic; keep `Action.payload_str` valid JSON and let validators enforce allowed states.
- Naming: snake_case for functions/variables, PascalCase for classes/enums, UPPER_SNAKE for constants and env keys.

## Testing Guidelines
- Mirror new logic with unit tests under `tests/`; use `monkeypatch` and fake OpenAI clients (see `test_brain_flow.py`) to keep runs deterministic.
- Mark any networked checks with `@pytest.mark.integration` and gate behind `RUN_OPENAI_INTEGRATION=1`.
- When adding new tools or states, add assertions for expected `tool_name`, `state`, and memory patches, and prefer fixed timestamps for reproducibility.

## Commit & Pull Request Guidelines
- Existing history uses short, imperative messages (“added visualization”, “version 3”); follow that tone and keep scope focused.
- In PRs, describe the scenario tested (e.g., `pytest`, integration flag, `scripts/run_scenarios.py` output), link issues, and include screenshots or logs for viewer or UX changes.
- Call out config needs (`OPENAI_API_KEY`, `OPENAI_MODEL_NAME`) and any new files to ignore (e.g., generated `.bulus/` data).

## Security & Configuration Tips
- Do not commit `.env` or real keys; placeholders like `sk-proj-твой-ключ-здесь` should be replaced locally only.
- Keep API calls deterministic (temperature 0/consistent model) to support reproducible replays and viewer traces.***
