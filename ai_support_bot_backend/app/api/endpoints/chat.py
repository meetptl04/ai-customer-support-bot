import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import crud, session, models
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage, ChatSession, UserChatSummary
from app.core import llm
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/{bot_id}/sessions", response_model=List[ChatSession])
def get_sessions_for_bot(
    bot_id: uuid.UUID,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.bot_id != bot_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    sessions = crud.get_user_chat_sessions(db, user_id=current_user.id, bot_id=bot_id)
    return sessions

@router.get("/summary/{session_id}", response_model=UserChatSummary)
def get_user_chat_summary(
    session_id: str,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    chat_history = crud.get_full_chat_history_by_session(db, session_id=session_id, user_id=current_user.id)
    if not chat_history:
        raise HTTPException(status_code=404, detail="Chat session not found or you do not have permission.")

    summary_text = llm.summarize_conversation_for_user(chat_history)
    return UserChatSummary(summary=summary_text, session_id=session_id)

@router.get("/history/{session_id}", response_model=List[ChatMessage])
def get_chat_history_for_session(
    session_id: str,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    history = crud.get_full_chat_history_by_session(db, session_id=session_id, user_id=current_user.id)
    if not history:
        raise HTTPException(status_code=404, detail="Chat session not found or you do not have permission to view it.")
    
    return history

@router.post("/{bot_id}", response_model=ChatResponse)
def chat_with_bot(
    bot_id: uuid.UUID,
    request: ChatRequest,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.bot_id != bot_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this bot",
        )
    
    chat_history = crud.get_chat_history(db, session_id=request.session_id, bot_id=bot_id, user_id=current_user.id)
    relevant_faqs = llm.get_relevant_faqs(query=request.message, faqs_data=current_user.bot.faqs)

    llm_output = llm.generate_llm_response(
        query=request.message,
        chat_history=chat_history,
        relevant_faqs=relevant_faqs,
        bot_name=current_user.bot.name 
    )
    response_text = llm_output.get("answer")
    suggestions = llm_output.get("suggestions")

    crud.create_chat_message(
        db, session_id=request.session_id, bot_id=bot_id, user_id=current_user.id, role="user", message=request.message
    )
    crud.create_chat_message(
        db, session_id=request.session_id, bot_id=bot_id, user_id=current_user.id, role="bot", message=response_text
    )

    return ChatResponse(response=response_text, suggested_actions=suggestions)

