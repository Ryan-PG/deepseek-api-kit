from fastapi import Request as FastAPIRequest
from fastapi_offline import FastAPIOffline
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
import time, json, os
from datetime import datetime
from common.api import DeepSeekAPI
from common.config import DEEPSEEK_API_KEY

app = FastAPIOffline()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = DeepSeekAPI(DEEPSEEK_API_KEY)

_sessions: Dict[str, dict] = {}

def get_session(session_id: Optional[str]) -> dict:
    """Get existing session or create a new one."""
    sid = session_id or "default_local_user"
    if sid not in _sessions:
        chat_id = api.create_chat_session()
        _sessions[sid] = {
            "chat_id": chat_id,
            "last_message_id": None,
            "thinking_enabled": True,
            "search_enabled": False,
            "last_message_preview": None,
        }
    return _sessions[sid]

# ---------- Models ----------
class ContentPart(BaseModel):
    type: str
    text: Optional[str] = None

class Message(BaseModel):
    content: Union[str, List[ContentPart]]

class ChatRequest(BaseModel):
    model_config = {"extra": "ignore"}

    messages: List[Message]
    stream: Optional[bool] = False
    session_id: Optional[str] = None

class SessionSettings(BaseModel):
    model_config = {"extra": "ignore"}

    thinking_enabled: Optional[bool] = None
    search_enabled: Optional[bool] = None

class SessionInfo(BaseModel):
    session_id: str
    chat_id: str
    thinking_enabled: bool
    search_enabled: bool
    last_message_preview: Optional[str] = None

# ---------- Helper ----------
def extract_content(content: Union[str, List[ContentPart]]) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(part.text or "" for part in content if part.type == "text")

def messages_to_chat(messages: List[Message]) -> str:
    """Extract last user message (history preserved via parent_message_id)."""
    if messages:
        return extract_content(messages[-1].content)
    return ""

# ---------- Middleware for logging ----------
@app.middleware("http")
async def log_time(request: FastAPIRequest, call_next):
    start = datetime.now()
    print(f"[{start.strftime('%H:%M:%S.%f')[:-3]}] --> {request.method} {request.url.path}")
    response = await call_next(request)
    end = datetime.now()
    print(f"[{end.strftime('%H:%M:%S.%f')[:-3]}] <-- {response.status_code} (took {(end-start).total_seconds():.2f}s)")
    return response

@app.get("/v1/sessions")
async def list_sessions():
    return [
        SessionInfo(
            session_id=sid,
            chat_id=session["chat_id"],
            thinking_enabled=session["thinking_enabled"],
            search_enabled=session["search_enabled"],
            last_message_preview=session.get("last_message_preview")
        )
        for sid, session in _sessions.items()
    ]

@app.patch("/v1/sessions/{session_id}/settings")
async def update_session_settings(session_id: str, settings: SessionSettings):
    session = get_session(session_id)
    if settings.thinking_enabled is not None:
        session["thinking_enabled"] = settings.thinking_enabled
    if settings.search_enabled is not None:
        session["search_enabled"] = settings.search_enabled
    return {"status": "updated", "session_id": session_id}

@app.delete("/v1/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id in _sessions:
        del _sessions[session_id]
        return {"status": "deleted"}
    return {"status": "not_found"}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    sid = request.session_id or "default_local_user"
    session = get_session(sid)
    chat_id = session["chat_id"]
    parent_message_id = session.get("last_message_id")

    prompt = messages_to_chat(request.messages)

    thinking = session.get("thinking_enabled")
    search = session.get("search_enabled")

    if request.stream:
        def generate():
            new_message_id = None
            full_response = ""

            for chunk in api.chat_completion(
                chat_id,
                prompt,
                parent_message_id=parent_message_id,
                thinking_enabled=thinking,
                search_enabled=search
            ):
                chunk_type = chunk.get("type")
                msg_id = chunk.get("response_message_id")

                if msg_id and not new_message_id:
                    new_message_id = msg_id

                if chunk_type == "thinking":
                    delta = {"reasoning_content": chunk.get("delta", "")}
                elif chunk_type == "content":
                    delta_text = chunk.get("delta", "")
                    full_response += delta_text
                    delta = {"content": delta_text}
                elif chunk_type == "finished":
                    if chunk.get("response_message_id"):
                        new_message_id = chunk["response_message_id"]
                    break
                else:
                    continue

                yield f"data: {json.dumps(delta)}\n\n"

            if new_message_id or full_response:
                if new_message_id:
                    session["last_message_id"] = new_message_id
                if full_response:
                    session["last_message_preview"] = full_response.strip().split("\n")[0][:100]

            yield f"data: {json.dumps({})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    # Non-streaming mode
    full_text = ""
    full_thinking = ""
    new_message_id = None

    for chunk in api.chat_completion(
        chat_id,
        prompt,
        parent_message_id=parent_message_id,
        thinking_enabled=thinking,
        search_enabled=search
    ):
        chunk_type = chunk.get("type")
        msg_id = chunk.get("response_message_id")

        if msg_id and not new_message_id:
            new_message_id = msg_id

        if chunk_type == "content":
            full_text += chunk.get("delta", "")
        elif chunk_type == "thinking":
            full_thinking += chunk.get("delta", "")
        elif chunk_type == "finished":
            if chunk.get("response_message_id"):
                new_message_id = chunk["response_message_id"]
            break

    if new_message_id:
        session["last_message_id"] = new_message_id
    if full_text:
        session["last_message_preview"] = full_text.strip().split("\n")[0][:100]

    return {"content": full_text, "reasoning_content": full_thinking}