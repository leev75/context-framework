# app/cli/main.py

from framework.context.conversation_manager import ConversationManager  # adjust path/name if different
from framework.context.llm_client import generate


SYSTEM_PROMPT = "You are a helpful assistant."  # placeholder — tweak wording as you like


def main() -> None:
    manager = ConversationManager()  # uses default db_path="data/context.db"
    session_id = manager.create_session()
    print(f"Session started: {session_id}")
    print("Type 'exit' or 'quit' to end.\n")

    while True:
        user_input = input("You: ")

        if not user_input.strip():
            continue

        if user_input.strip().lower() in ("exit", "quit"):
            break

        manager.add_message(session_id, "user", user_input)
        history = manager.get_history(session_id)

        # TODO: generate() can raise LLMClientError (per Day 3). Right now
        # an exception here crashes the whole loop and the user_message is
        # already saved but no assistant reply follows. Decide: catch it here
        # and print an error but keep the loop alive? Or let it crash?
        reply = generate(history, SYSTEM_PROMPT)

        print(f"Assistant: {reply}\n")
        manager.add_message(session_id, "assistant", reply)


if __name__ == "__main__":
    main()
