import uuid
import json
import csv
import io
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db import crud, session, models
from app.schemas.bot import Bot
from app.api.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=Bot, status_code=status.HTTP_201_CREATED)
def create_new_bot(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(session.get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.bot_id is not None:
        raise HTTPException(status_code=403, detail="Only admin users can create bots.")

    faqs_data = []
    contents = file.file.read()

    if file.filename.endswith('.json'):
        try:
            data = json.loads(contents)
            if isinstance(data, list) and all('question' in item and 'answer' in item for item in data):
                faqs_data = data
            else:
                raise HTTPException(status_code=400, detail="Invalid JSON format.")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file.")

    elif file.filename.endswith('.csv'):
        try:
            csv_file = io.StringIO(contents.decode('utf-8'))
            reader = csv.DictReader(csv_file)
            for row in reader:
                if 'question' in row and 'answer' in row:
                    faqs_data.append({"question": row['question'], "answer": row['answer']})
                else:
                    raise HTTPException(status_code=400, detail="CSV must have 'question' and 'answer' columns.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing CSV file: {e}")
            
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format: .json or .csv only.")

    if not faqs_data:
        raise HTTPException(status_code=400, detail="No valid FAQ data found in the uploaded file.")

    return crud.create_bot(db=db, name=name, faqs_data=faqs_data, owner_id=current_user.id)

@router.get("/", response_model=List[Bot])
def read_user_bots(db: Session = Depends(session.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.bot_id is not None:
        raise HTTPException(status_code=403, detail="Only admin users can view bots.")
    return crud.get_bots_by_owner(db, owner_id=current_user.id)
