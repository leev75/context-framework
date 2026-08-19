from dotenv import load_dotenv
load_dotenv()  # only needed if you're using the .env approach

from framework.models.models import Message 
from framework.context.llm_client import generate

messages = [
    Message(session_id="test-session", role="user", content="Say hello in exactly 5 words."),
]

result = generate(messages, system_prompt="You are a terse assistant.")
print("COMPLETION:", result)