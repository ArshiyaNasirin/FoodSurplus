"""
routers/chat.py - LangChain-powered AI Chatbot endpoints with multi-provider support.

Supported Providers:
  1. xAI Grok (Cloud API)  - High-intelligence cloud reasoning using XAI_API_KEY
  2. Ollama Qwen (Local)   - Offline, private local LLM running on port 11434

Features:
  - Dynamic user provider selection ('xai' vs 'ollama')
  - LangChain-managed prompt templates, history formatting, and model invocations
  - Graceful multi-tier fallback (fallback between models or to built-in domain rules)
  - Persistent conversation memory stored in SQLite
  - Provider availability introspection endpoint for real-time frontend indicators
"""

import os
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ChatMessage
from backend.schemas import ChatRequest, ChatResponse, ProvidersResponse, ProviderInfo
from backend.services.chat_service import (
    get_ai_response_sync,
    get_all_providers_info,
    is_fallback_enabled,
    normalize_provider_name
)

router = APIRouter(tags=["AI Chat Assistant"])


@router.get("/chat/providers", response_model=ProvidersResponse)
def get_providers():
    """
    Introspect available AI providers, their online status, and active models.
    Enables frontend UI to display real-time availability badges.
    """
    providers_data = get_all_providers_info()
    default_p = normalize_provider_name(os.getenv("DEFAULT_AI_PROVIDER", "xai"))
    fallback_on = is_fallback_enabled()
    
    return ProvidersResponse(
        default_provider=default_p,
        fallback_enabled=fallback_on,
        providers=[ProviderInfo(**p) for p in providers_data]
    )


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a message to FoodBridge and receive an intelligent response.
    
    - session_id: Unique conversation thread identifier
    - message: The user query, recipe request, or food surplus question
    - provider: 'xai' (cloud Grok) or 'ollama' (local Qwen)
    - use_ollama: (Legacy bool) True = local Qwen, False = cloud Grok
    """
    target_provider = request.provider
    if request.use_ollama is True:
        target_provider = "ollama"
    elif request.use_ollama is False and not request.provider:
        target_provider = "xai"
    
    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == request.session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(20)
        .all()
    )
    history = [{"role": msg.role, "content": msg.content} for msg in history_rows]
    
    result = get_ai_response_sync(
        user_input=request.message,
        history=history,
        provider=target_provider,
        allow_fallback=is_fallback_enabled()
    )
    
    reply_text = result["reply"]
    model_used = result["model_used"]
    provider_used = result["provider_used"]
    status = result["status"]
    fallback_notice = result.get("fallback_notice")
    
    try:
        db.add(ChatMessage(session_id=request.session_id, role="user", content=request.message))
        db.add(ChatMessage(session_id=request.session_id, role="assistant", content=reply_text))
        db.commit()
    except Exception as db_err:
        db.rollback()
        print(f"Warning: Failed to persist chat message to SQLite: {db_err}")
    
    return ChatResponse(
        session_id=request.session_id,
        reply=reply_text,
        model_used=model_used,
        provider=provider_used,
        status=status,
        fallback_notice=fallback_notice
    )


@router.get("/chat/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    """Retrieve full conversation history for a given session."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if hasattr(m, "created_at") and m.created_at else None
        }
        for m in messages
    ]


@router.delete("/chat/{session_id}")
def clear_history(session_id: str, db: Session = Depends(get_db)):
    """Clear all chat messages associated with a session ID."""
    deleted_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.commit()
    return {"message": f"Cleared {deleted_count} messages for session '{session_id}'"}
