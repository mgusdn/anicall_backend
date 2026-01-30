from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime


import models, database, schemas
from database import engine, get_db


import os
from dotenv import load_dotenv
from openai import OpenAI


from fastapi.responses import HTMLResponse # 추가
from fastapi.staticfiles import StaticFiles # 필요시 추가
from fastapi.templating import Jinja2Templates # 추가
from fastapi import Request # 추가


# .env 파일 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# templates 설정
templates = Jinja2Templates(directory="templates")


# 서버 시작 시 DB 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Webtoon Character Chat API")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # 이제 http://127.0.0.1:8000/ 에 접속하면 templates/index.html을 보여줍니다.
    return templates.TemplateResponse("index.html", {"request": request})


# --- 1. 사용자 API ---
@app.post("/api/users/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- 2. 캐릭터 API ---
@app.post("/api/characters", response_model=schemas.CharacterResponse)
def create_character(character: schemas.CharacterCreate, db: Session = Depends(get_db)):
    db_character = models.Character(**character.dict())
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character

@app.get("/api/characters", response_model=List[schemas.CharacterResponse])
def list_characters(db: Session = Depends(get_db)):
    return db.query(models.Character).all()

# --- 3. 채팅방 API ---
@app.post("/api/chat/rooms", response_model=schemas.ChatRoomResponse)
def create_room(room: schemas.ChatRoomCreate, db: Session = Depends(get_db)):
    # 이미 방이 있는지 확인
    existing_room = db.query(models.ChatRoom).filter(
        models.ChatRoom.user_id == room.user_id,
        models.ChatRoom.character_id == room.character_id
    ).first()
    if existing_room:
        return existing_room
    
    db_room = models.ChatRoom(user_id=room.user_id, character_id=room.character_id)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

# --- 4. 메시지 API (채팅 주고받기) ---

@app.get("/api/chat/rooms/{room_id}/messages", response_model=List[schemas.MessageResponse])
def get_messages(room_id: int, db: Session = Depends(get_db)):
    return db.query(models.Message).filter(models.Message.room_id == room_id).all()



@app.post("/api/chat/rooms/{room_id}/messages", response_model=schemas.MessageResponse)
def send_message(room_id: int, message: schemas.MessageCreate, db: Session = Depends(get_db)):
    print(f"--- 메시지 수신: {message.content} ---") # 터미널 확인용
    
    # 1. 사용자 메시지 저장
    user_msg = models.Message(room_id=room_id, sender="user", content=message.content)
    db.add(user_msg)
    db.commit()

    # 2. 정보 가져오기
    room = db.query(models.ChatRoom).filter(models.ChatRoom.id == room_id).first()
    if not room:
        print("에러: 방을 찾을 수 없음")
        raise HTTPException(status_code=404, detail="Room not found")

    # 3. OpenAI 호출
    print("OpenAI 답변 생성 중...")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"당신은 {room.character.name}입니다. 성격: {room.character.persona}"},
                {"role": "user", "content": message.content}
            ]
        )
        ai_content = response.choices[0].message.content
        print(f"AI 답변 완료: {ai_content}") # 답변이 잘 생성됐는지 확인
    except Exception as e:
        print(f"OpenAI 에러 발생: {e}")
        raise HTTPException(status_code=500, detail="OpenAI API Error")

    # 4. 봇 메시지 저장
    bot_msg = models.Message(room_id=room_id, sender="bot", content=ai_content)
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)
    
    print("DB 저장 완료!")
    return bot_msg