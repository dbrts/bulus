# Bulus

**Debug AI Agents like never before.**

Bulus is a deterministic state management and replay engine for LLM agents, built on the **Stateless Brain** pattern. It treats agent sessions as an immutable memory ledger ("Ice"), enabling you to freeze, rewind, and fork production sessions for advanced debugging and analysis.

## Core Concepts

### 1. The Stateless Brain
In Bulus, the agent has no internal mutable state. Its "brain" is a pure function that takes the entire session Ice ledger as input and returns the next action.

```python
Action = f(Ice)
```

This ensures that for any given Ice ledger, the agent's decision is deterministic (assuming the LLM's temperature is 0 or consistent).

### 2. Ice: The Immutable Ledger
The agent's memory is not a black box vector store or a mutable JSON object. It is a linear, append-only log of events called "Ice".

Each entry in the Ice is a tuple:
```python
(
    timestamp,   # When it happened
    tool_name,   # What tool triggered the event (e.g., 'user_said', 'update')
    payload,     # Data associated with the tool
    state,       # The FSM state of the agent AFTER this event
    storage,     # The agent's memory/variables AFTER this event
    thought      # The reasoning behind the action (if applicable)
)
```

### 3. Time Travel & Forking
Because the state is fully reconstructed from Ice, you can:
- **Rewind:** Slice the Ice list to go back to any point in time.
- **Fork:** Create a new branch of the conversation by appending a different event to past Ice.
- **Debug:** Replay a failed production session in a local environment (like a Jupyter Notebook) to understand exactly why the agent made a specific decision.

## Installation

```bash
git clone https://github.com/dbrts/bulus.git
cd bulus
pip install -e .
```

## Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
```

## Quick Start

Here is a simple example of how the Stateless Brain works (derived from `scripts/run_scenarios.py`):

```python
import time
from bulus.brain.worker import stateless_brain
from bulus.core.states import AgentState
from bulus.runner.tools import apply_update

# 1. Define an initial Ice ledger (e.g., user greets the agent)
t0 = time.time()
ice = [
    (t0, "send_message", {"text": "Hello! What is your name?"}, AgentState.ASK_NAME.value, {}, "Init"),
    (t0 + 1, "user_said", "I am Alice", AgentState.ASK_NAME.value, {}, None),
]

# 2. Call the brain to get the next action
action = stateless_brain(ice)

print(f"Thought: {action.thought}")
print(f"Tool:    {action.tool_name}")
print(f"Payload: {action.payload}")

# Expected Output:
# Thought: The user provided their name. I should update my memory and move to the next state.
# Tool:    update
# Payload: {'state': 'ask_age', 'memory': {'name': 'Alice'}}
```

## Project Structure

- **`src/bulus/brain`**: The decision-making logic (`stateless_brain`). Prompts the LLM.
- **`src/bulus/core`**: Data schemas (`IceEntry`, `Action`) and State Machine definitions.
- **`src/bulus/runner`**: Executes actions returned by the brain.
- **`src/bulus/storage`**: Manages the persistence of the Ice ledger.
- **`src/bulus/engine`**: Orchestrates the loop.
- **`viewer/`**: Contains the Time Travel Debugger visualization tools.
- **`.bulus/sessions/<id>.json`**: Per-session JSON with `metadata` (e.g., `status: need_brain | need_runner | still`) and `history` (list of Ice entries).

## Visualization (Time Travel Viewer)

Bulus includes a "Time Travel" HTML viewer for Jupyter Notebooks. It allows you to replay sessions with a slider, inspecting the state and memory at each step.

```python
from viewer import show_bulus_trace
# Assuming you have an Ice list (e.g., from BulusRepo or a script)
# ice = [...] 

show_bulus_trace(ice)
```

## License

Apache 2.0
