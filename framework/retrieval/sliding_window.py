
from framework.models.models import Message


def sliding_window(messages: list[Message], max_turns: int) -> list[Message]:
    if max_turns <= 0:
        raise ValueError("max_turns must be a positive integer.")

    # Step 1: collect the indices of every user message, in order
    user_indices = [i for i, m in enumerate(messages) if m.role == "user"]

    # Step 2: fewer (or equal) user turns than requested -> return everything
    if len(user_indices) <= max_turns:
        return messages

    # Step 3: find the index where the window should START
    # (the index of the user message that begins the max_turns-th-from-the-end turn)
    start_index = user_indices[-max_turns]

    # Step 4: slice once
    return messages[start_index:]