import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load variable dari file .env
load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Konfigurasi engine. (Untuk SQLite tambahkan argumen: connect_args={"check_same_thread": False})
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency untuk mendapatkan session DB di route nanti
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()