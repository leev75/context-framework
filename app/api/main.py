from framework.context.conversation_manager import ConversationManager
from fastapi import FastAPI, HTTPException
from app.api.schemas import SessionResponse,ChatRequest, ChatResponse ,HistoryResponse
from framework.context.llm_client import generate, LLMClientError
from framework.context.conversation_manager import SessionNotFoundError


app = FastAPI()

@app.post("/session", response_model=SessionResponse)
def create_session():
    manager = ConversationManager()
    session_id = manager.create_session()
    return SessionResponse(session_id=session_id)

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    manager = ConversationManager()
    try:
        manager.add_message(request.session_id, "user", request.message)
        history = manager.get_history(request.session_id)
        SYSTEM_PROMPT = "You are a helpful assistant."  # placeholder — tweak wording as you like
        reply = generate(history, SYSTEM_PROMPT)
        manager.add_message(request.session_id, "assistant", reply)
        return ChatResponse(session_id=request.session_id, reply=reply)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except LLMClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/session/{session_id}", response_model=HistoryResponse )
def get_session(session_id: str):
    manager = ConversationManager()
    try:
        history = manager.get_history(session_id)
        return  HistoryResponse(session_id=session_id, messages=history)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")