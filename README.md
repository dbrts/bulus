# Bulus

![bulus_demo_1080](https://github.com/user-attachments/assets/c77be429-b112-40cc-a994-e014bdca1f83)

**Time-Travel Debugging for Conversational AI.**

Bulus is a deterministic framework designed specifically for building **conversational agents** that you can actually debug. It treats an agent's entire lifecycle as an immutable sequence of events (the "Ice" ledger), allowing you to **freeze, rewind, and fork** complex conversations to understand exactly *why* an agent made a specific decision.

## Why Bulus?

Building conversational agents is hard. Debugging them is harder.
- **The Problem:** When an agent hallucinations 10 turns into a conversation, reproducing that exact state is often impossible. Traditional agents rely on mutable memory objects and hidden internal states that change unpredictably.
- **The Solution:** Bulus removes mutable state entirely from the agent's logic.

## Core Concepts

### 1. The Stateless Brain
In Bulus, the agent is a **pure function**. It has no internal memory. Instead, its "brain" takes the entire conversation history (the ledger) as input and outputs a single action.

```python
Action = f(Conversation_History)
```

This guarantees **determinism**: given the same history, the agent will always make the same decision (assuming a constant LLM temperature).

### 2. Ice: The Conversation Ledger
We call the agent's memory **"Ice"**. It is a linear, append-only log of every event in the conversation.

Each entry captures the exact context of a moment:
```python
(
    timestamp,   # When it happened
    tool_name,   # The action taken (e.g., 'user_said', 'search_db')
    payload,     # Data (e.g., the user's message, search results)
    state,       # The FSM state AFTER this event
    storage,     # Variables/Memory snapshot AFTER this event
    thought      # The agent's reasoning (Chain of Thought)
)
```

### 3. Time Travel & Forking
Because the entire state is reconstructed from the Ice ledger, you can:
- **Rewind:** Slice the ledger to go back to turn #5.
- **Fork:** Insert a different user response or tool output at turn #5 to create a parallel conversation universe.
- **Debug:** Replay a production failure in a local environment (like a Jupyter Notebook) to inspect the agent's "thought" process step-by-step.

## Installation

```bash
git clone https://github.com/dbrts/bulus.git
cd bulus
uv sync                 # Creates .venv and installs dependencies
# For development (tests/linting):
# uv sync --extra dev
```

## Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
```

## Quick Start: A Simple Conversation

Here is how a basic conversational loop works using the Stateless Brain.

```python
import time
from bulus.brain.worker import stateless_brain
from bulus.core.states import AgentState

# 1. Initialize the Ledger ("Ice") with the start of a conversation
t0 = time.time()
ice = [
    # The agent decides to ask for the name
    (t0, "send_message", {"text": "Hello! What is your name?"}, AgentState.ASK_NAME.value, {}, "Init"),
    # The user responds
    (t0 + 1, "user_said", "I am Alice", AgentState.ASK_NAME.value, {}, None),
]

# 2. Invoke the Brain
# The brain reads the history and decides what to do next.
action = stateless_brain(ice)

print(f"Thought: {action.thought}")
print(f"Action:  {action.tool_name}")
print(f"Data:    {action.payload}")

# Expected Output:
# Thought: The user provided their name 'Alice'. I need to update my memory.
# Action:  update
# Data:    {'state': 'ask_age', 'memory': {'name': 'Alice'}}
```

## Visualization

Bulus includes a **Time Travel Viewer** for Jupyter Notebooks. It provides a visual slider to replay the conversation, inspecting the exact state and memory changes at every single turn.

```python
from viewer import show_bulus_trace
# Pass your Ice ledger to the viewer
show_bulus_trace(ice)
```

## Project Structure

- **`src/bulus/brain`**: The cognitive engine. Contains prompts and the `stateless_brain` logic.
- **`src/bulus/core`**: Schemas for `IceEntry`, `Action`, and State Machine definitions.
- **`src/bulus/engine`**: Orchestrates the main conversational loop.
- **`src/bulus/storage`**: Manages persistence of the Ice ledger.
- **`viewer/`**: HTML/JS tools for visualizing trace logs.

## License

Apache 2.0
