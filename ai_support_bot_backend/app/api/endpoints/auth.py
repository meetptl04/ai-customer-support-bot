import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db import crud, session, models
from app.schemas.user import UserCreate, User
from app.schemas.token import Token
from app.core import security

router = APIRouter()

@router.post("/admin/register", response_model=User, status_code=status.HTTP_201_CREATED)
def create_admin_user(user: UserCreate, db: Session = Depends(session.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email, models.User.bot_id == None).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email already registered",
        )
    return crud.create_user(db=db, user=user, bot_id=None)

@router.post("/{bot_id}/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user_for_bot(bot_id: uuid.UUID, user: UserCreate, db: Session = Depends(session.get_db)):
    db_bot = crud.get_bot(db, bot_id=bot_id)
    if not db_bot:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    db_user = crud.get_user_by_email_and_bot(db, email=user.email, bot_id=bot_id)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered for this bot",
        )
    return crud.create_user(db=db, user=user, bot_id=bot_id)

@router.post("/admin/login", response_model=Token)
def login_admin(db: Session = Depends(session.get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(models.User).filter(models.User.email == form_data.username, models.User.bot_id == None).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect admin email or password")
    access_token = security.create_access_token(data={"sub": user.email}) 
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/{bot_id}/login", response_model=Token)
def login_user_for_bot(bot_id: uuid.UUID, db: Session = Depends(session.get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_email_and_bot(db, email=form_data.username, bot_id=bot_id)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password for this bot",
        )
    access_token = security.create_access_token(data={"sub": user.email, "bot_id": user.bot_id})
    return {"access_token": access_token, "token_type": "bearer"}

