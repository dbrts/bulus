import time

from bulus.brain.worker import stateless_brain
from bulus.core.schemas import IceEntry
from bulus.runner.worker import imperative_runner
from bulus.storage.repository import BulusRepo


def run_session_loop(session_id: str):
    print(f"🧊 Bulus Engine started for session: {session_id}")
    repo = BulusRepo(session_id)

    while True:
        # 1. Загрузка
        doc = repo.load()
        ice = doc.get("history", [])
        status = doc.get("metadata", {}).get("status", "need_brain")

        # ЛОГИКА ОЖИДАНИЯ ЮЗЕРА:
        # если статус still — ждем пользователя; иначе даем ход мозгу.
        wait_for_user = status == "still"

        if wait_for_user:
            try:
                user_text = input("\nUSER > ")
            except KeyboardInterrupt:
                break

            if user_text.lower() in ["exit", "q"]:
                break

            # Создаем Ice событие от юзера
            # Берем стейт/сторадж из последнего кадра
            state = ice[-1][3]
            storage = ice[-1][4]

            user_entry: IceEntry = (
                time.time(),
                "user_said",
                user_text,  # Payload у user_said просто строка
                state,
                storage,
                None,  # У юзера нет мыслей
            )
            repo.append(user_entry, status="need_brain")
            continue

        # 2. BRAIN STEP
        print("🧠 Thinking...")
        action = stateless_brain(ice)
        print(f"   [Thought]: {action.thought}")
        print(f"   [Tool]:    {action.tool_name} | {action.payload}")

        # 3. RUNNER STEP
        new_ice = imperative_runner(ice, action)

        # 4. SAVE (COMMIT)
        repo.append(new_ice, status="still")

        time.sleep(0.5)


if __name__ == "__main__":
    run_session_loop("demo_session")
