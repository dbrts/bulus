import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Try to import IPython for Jupyter display, but don't fail if not present
try:
    from IPython.display import HTML, display
except ImportError:
    HTML = None
    display = None


def _load_template() -> str:
    """Loads the HTML template from the same directory as this script."""
    template_path = Path(__file__).parent / "template.html"
    return template_path.read_text(encoding="utf-8")


def show_bulus_trace(ice: List[Tuple[float, str, Dict[str, Any], str, Dict[str, Any], str | None]], height: int = 600):
    """
    Renders the Bulus Time Travel Viewer in a Jupyter Notebook.

    Args:
        ice: The IceHistory list from bulus.
        height: Height of the viewer in pixels.
    """
    if HTML is None:
        print("Error: IPython is not installed. Cannot render HTML in this environment.")
        return

    # Serialize ice to JSON safely
    # We might need to handle non-serializable objects if they sneak into storage,
    # but Bulus core schemas seem to enforce dicts/strings.
    try:
        json_ice = json.dumps(ice)
    except TypeError:
        # Fallback for safe serialization
        json_ice = json.dumps(ice, default=str)

    html_template = _load_template()

    # Inject data into the script tag
    injection_code = f"var iceData = {json_ice};"
    final_html = html_template.replace("var iceData = []; // DATA_INJECTION_POINT", injection_code)

    # Wrap in iframe-like container if needed, but direct HTML usually works better
    # for sizing in modern Jupyter.
    # However, to avoid CSS conflicts with the notebook itself, using an IFrame is safer,
    # but constructing a raw HTML object with scoped styles is easier for now.
    # Since we used specific class names and an iframe might be tricky with local file loading (not here since we inject string),
    # let's try direct HTML injection first.

    # NOTE: Direct HTML injection in Jupyter shares the DOM.
    # To prevent global CSS pollution (like 'body { margin: 0 }'),
    # we should wrap the content in a div or use shadow DOM.
    # Or simply relying on IFrame is the robust "Viewer" way.

    iframe_html = f"""
    <iframe srcdoc="{final_html.replace('"', "&quot;")}" width="100%" height="{height}px" style="border: none; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></iframe>
    """

    display(HTML(iframe_html))


if __name__ == "__main__":
    # Test block for running this script directly
    import time

    # Mock data based on scripts/run_scenarios.py (Multi-turn)
    t0 = time.time()

    # 1. Start: Agent asks name
    ice_entries = [
        (t0 + 1, "send_message", {"text": "Как тебя зовут?"}, "ask_name", {}, "Start session"),
        (t0 + 2, "user_said", "Меня зовут Семен", "ask_name", {}, None),
    ]

    # 2. Brain decides to update state -> ask_age
    # Note: 'update' tool entry shows the RESULTING state/storage in the tuple slots 3 & 4
    mem_v1 = {"name": "Semen"}
    ice_entries.append(
        (
            t0 + 3,
            "update",
            {"state": "ask_age", "memory": mem_v1},
            "ask_age",
            mem_v1,
            "User provided name. Moving to ask_age.",
        )
    )

    # 3. Agent asks age
    ice_entries.append(
        (
            t0 + 4,
            "send_message",
            {"text": "Приятно познакомиться, Семен! Сколько тебе лет?"},
            "ask_age",
            mem_v1,
            "Ask age",
        )
    )
    ice_entries.append((t0 + 5, "user_said", "Мне сейчас 25", "ask_age", mem_v1, None))

    # 4. Brain decides to update state -> ask_occupation
    mem_v2 = {"name": "Semen", "age": 25}
    ice_entries.append(
        (
            t0 + 6,
            "update",
            {"state": "ask_occupation", "memory": {"age": 25}},
            "ask_occupation",
            mem_v2,
            "User provided age. Moving to ask_occupation.",
        )
    )

    # 5. Agent asks occupation
    ice_entries.append(
        (
            t0 + 7,
            "send_message",
            {"text": "Супер, 25 — отличный возраст! А кем работаешь?"},
            "ask_occupation",
            mem_v2,
            "Ask job",
        )
    )
    ice_entries.append((t0 + 8, "user_said", "Я работаю AI инженером", "ask_occupation", mem_v2, None))

    # 6. Brain decides to update state -> call_ping (Ready)
    mem_v3 = {"name": "Semen", "age": 25, "occupation": "AI engineer"}
    ice_entries.append(
        (
            t0 + 9,
            "update",
            {"state": "call_ping", "memory": {"occupation": "AI engineer"}},
            "call_ping",
            mem_v3,
            "User provided occupation. All data collected.",
        )
    )

    print("Writing test_output.html...")
    with open("test_output.html", "w") as f:
        # Manually inject for local test
        tmpl = _load_template()
        code = f"var iceData = {json.dumps(ice_entries)};"
        f.write(tmpl.replace("var iceData = []; // DATA_INJECTION_POINT", code))
    print("Done. Open test_output.html to view.")
