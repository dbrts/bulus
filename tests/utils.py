from typing import List

from bulus.core.schemas import Action


def make_fake_client(actions_queue: List[Action]):
    """
    Returns a fake OpenAI-like client with a deterministic queue of Actions.
    Each call to parse() pops the next Action; raises AssertionError if queue is empty.
    """

    class _FakeResponse:
        def __init__(self, action: Action):
            self.choices = [type("Choice", (), {"message": type("Msg", (), {"parsed": action})()})()]

    class _FakeCompletions:
        def __init__(self, queue: List[Action]):
            self._queue = list(queue)

        def parse(self, **kwargs):
            if not self._queue:
                raise AssertionError("No actions left in fake completions queue")
            action = self._queue.pop(0)
            return _FakeResponse(action)

    class _FakeClient:
        def __init__(self, queue: List[Action]):
            self.beta = type("Beta", (), {"chat": type("Chat", (), {"completions": _FakeCompletions(queue)})()})()

    return _FakeClient(actions_queue)
