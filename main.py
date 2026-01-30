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
async def home(request: Request):
    # 이제 루트 경로는 캐릭터 선택 화면을 보여줍니다.
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/chat/{room_id}", response_class=HTMLResponse)
async def chat_page(request: Request, room_id: int):
    # /chat/1 혹은 /chat/2로 접속하면 채팅창을 보여줍니다.
    return templates.TemplateResponse("index.html", {"request": request, "room_id": room_id})


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
        # 1. 사용할 데이터를 함수 밖에서 미리 정의합니다.
        char = room.character
        
        # 2. 시스템 메시지 내용을 변수로 미리 빼두면 코드가 훨씬 깔끔해집니다.
        prompt_content = (
            f"당신은 웹툰 '{char.webtoon_title}'의 캐릭터 '{char.name}'입니다.\n"
            f"다음 정보를 바탕으로 캐릭터에 완전히 빙의해서 대화하세요.\n\n"
            f"[프로필]\n"
            f"- 학교: {char.school}\n"
            f"- 나이: {char.age}세\n"
            f"- 특징: {char.physical}, {char.bloodtype}, {char.location} 거주\n"
            f"- 가족: {char.family}\n"
            f"- 좋아하는 것: {char.likes}\n"
            f"- 싫어하는 것: {char.dislikes}\n\n"
            f"[성격 및 말투]\n"
            f"- 성격: {char.personality}\n"
            f"- 말투: {char.speech_style}"
        )

        # 3. 이제 함수를 호출합니다.
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt_content},
                {"role": "user", "content": message.content}
            ]
        )
        
        ai_content = response.choices[0].message.content
        print(f"AI 답변 완료: {ai_content}") 
        
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