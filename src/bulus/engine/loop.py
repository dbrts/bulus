import time
from bulus.storage.repository import BulusRepo
from bulus.brain.worker import stateless_brain
from bulus.runner.worker import imperative_runner
from bulus.core.schemas import IceEntry


def run_session_loop(session_id: str):
    print(f"🧊 Bulus Engine started for session: {session_id}")
    repo = BulusRepo(session_id)

    while True:
        # 1. Загрузка
        ice = repo.load_ice()

        # ЛОГИКА ОЖИДАНИЯ ЮЗЕРА:
        # Если ледник пуст ИЛИ последнее действие агента было 'send_message',
        # значит теперь очередь юзера.
        wait_for_user = False
        if not ice:
            wait_for_user = False  # Сразу даем агенту инициативу (приветствие)
        else:
            last_tool = ice[-1][1]
            if last_tool in ["send_message", "test_ping", "error"]:
                wait_for_user = True

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
            repo.append(user_entry)
            continue

        # 2. BRAIN STEP
        print("🧠 Thinking...")
        action = stateless_brain(ice)
        print(f"   [Thought]: {action.thought}")
        print(f"   [Tool]:    {action.tool_name} | {action.payload}")

        # 3. RUNNER STEP
        new_ice = imperative_runner(ice, action)

        # 4. SAVE (COMMIT)
        repo.append(new_ice)

        time.sleep(0.5)


if __name__ == "__main__":
    run_session_loop("demo_session")
