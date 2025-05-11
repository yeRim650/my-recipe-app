from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:1234@localhost/cookwise"
)

# SQLModel 기반 엔진 생성 (단 한 번만!)
engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = Session

# DB 테이블 생성 (애플리케이션 시작 시 호출)
def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
