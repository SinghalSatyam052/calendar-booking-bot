from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.schema import ChatMessage

from .agent import booking_agent

app = FastAPI(title="Calendar Booking Bot")

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    suggestions: list | None = None
    tool_calls: list | None = None

_sessions: dict[str, list[ChatMessage]] = {}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    history = _sessions.setdefault(req.session_id, [])
    history.append(ChatMessage(role="user", content=req.message))

    try:
        # ‼️ agent expects {"input": ...}.   adjust if you’ve configured differently
        result = await booking_agent.ainvoke({"input": req.message})
        print("🔍 raw agent result:", result)

        # --- normalize result ---------------------------------------------
        if isinstance(result, dict):
            answer       = result.get("output") or result.get("answer") or ""
            tool_calls   = result.get("tool_calls") or None
            suggestions  = result.get("suggestions") or None
        else:  # it's a plain string (or another primitive)
            answer      = str(result)
            tool_calls  = None
            suggestions = None
        # ------------------------------------------------------------------

        history.append(ChatMessage(role="assistant", content=answer))
        return ChatResponse(
            session_id=req.session_id,
            answer=answer,
            tool_calls=tool_calls,
            suggestions=suggestions,
        )

    except Exception as e:
        import traceback, sys
        print("❌ ERROR in /chat ------------------------------------------------")
        traceback.print_exc(file=sys.stdout)
        print("------------------------------------------------------------------")
        # Still return 500 so Streamlit knows it failed, but with readable text
        raise HTTPException(status_code=500, detail=str(e)) from e
