from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. DB 파일 경로 설정 (현재 폴더에 webtoon.db라는 이름으로 생성됨)
SQLALCHEMY_DATABASE_URL = "sqlite:///./webtoon.db"

# 2. DB 엔진 생성
# SQLite는 기본적으로 멀티스레드 접근을 제한하지만, FastAPI와 함께 쓰기 위해 
# check_same_thread=False 설정을 추가합니다.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. 데이터베이스와 통신하기 위한 세션 클래스 생성
# autoflush=False: 커밋 전까지 데이터를 자동으로 반영하지 않음
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 나중에 만들 DB 모델들이 상속받을 기본 클래스
Base = declarative_base()

# 5. DB 세션을 가져오기 위한 의존성 함수 (나중에 API에서 사용)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()