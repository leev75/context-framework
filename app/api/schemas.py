from pydantic import BaseModel
from framework.models.models import Message

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str

class SessionResponse(BaseModel):
    session_id: str

class HistoryResponse(BaseModel):
    session_id: str
    messages: list[Message]