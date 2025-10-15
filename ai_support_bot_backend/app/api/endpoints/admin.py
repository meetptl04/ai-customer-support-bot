from typing import List 
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import crud, session, models
from app.schemas.chat import UserChatSummary, AnalyticsReport
from app.core import llm
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/bots/{bot_id}/summaries", response_model=List[UserChatSummary])
def get_all_bot_summaries(
    bot_id: uuid.UUID,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_bot = crud.get_bot(db, bot_id=bot_id)
    if not db_bot or current_user.id != db_bot.owner_id:
        raise HTTPException(status_code=403, detail="Permission denied.")

    summaries = crud.get_all_summaries_for_bot(db, bot_id=bot_id)
    return [{"summary": s.summary_text, "session_id": s.session_id} for s in summaries]

@router.post("/bots/{bot_id}/process-summaries", status_code=status.HTTP_202_ACCEPTED)
def process_new_chat_summaries(
    bot_id: uuid.UUID,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.bot_id is not None or current_user.id != crud.get_bot(db, bot_id).owner_id:
        raise HTTPException(status_code=403, detail="Permission denied.")

    unsummarized = crud.get_unsummarized_sessions(db, bot_id=bot_id)
    if not unsummarized:
        return {"message": "No new chat sessions to process."}

    processed_count = 0
    for session_info in unsummarized:
        full_history = crud.get_full_chat_history_by_session(db, session_id=session_info.session_id, user_id=session_info.user_id)
        if full_history:
            # UPDATED: Call the new admin-specific summary function
            summary_text = llm.summarize_conversation_for_admin(full_history)
            crud.create_chat_summary(db, bot_id=bot_id, session_id=session_info.session_id, summary_text=summary_text)
            processed_count += 1
    
    return {"message": f"Successfully processed and stored {processed_count} new chat summaries."}

@router.get("/bots/{bot_id}/analytics", response_model=AnalyticsReport)
def get_bot_analytics(
    bot_id: uuid.UUID,
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_bot = crud.get_bot(db, bot_id=bot_id)
    if current_user.bot_id is not None or current_user.id != db_bot.owner_id:
        raise HTTPException(status_code=403, detail="Permission denied.")

    summaries_from_db = crud.get_all_summaries_for_bot(db, bot_id=bot_id)
    if not summaries_from_db:
        raise HTTPException(status_code=404, detail="No summary data available for this bot. Run processing first.")

    summary_texts = [s.summary_text for s in summaries_from_db]
    analytics_data = llm.generate_analytics_summary(summary_texts)

    return AnalyticsReport(
        bot_name=db_bot.name,
        total_summaries_analyzed=len(summary_texts),
        **analytics_data
    )
