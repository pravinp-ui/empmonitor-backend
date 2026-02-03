from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Render PostgreSQL (auto-detected!)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "postgresql://localhost"  # Fallback for local testing

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "🚀 Employee Monitor API LIVE 🚀 PostgreSQL v2!"}

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "OK", "database": "✅ PostgreSQL SQLAlchemy CONNECTED!"}
    except Exception as e:
        return {"status": "Server OK", "database": f"❌ Error: {str(e)}"}

@app.post("/auth/register")
def register(user: UserRegister):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT id FROM users WHERE username = :username OR email = :email"),
                {"username": user.username, "email": user.email}
            )
            if result.fetchone():
                raise HTTPException(400, "User exists")
            
            connection.execute(
                text("INSERT INTO users (username, email, password, created_at) VALUES (:username, :email, :password, NOW())"),
                {"username": user.username, "email": user.email, "password": user.password}
            )
            connection.commit()
            
            result = connection.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": user.username}
            )
            user_id = result.fetchone()[0]
            
        return {"message": "✅ User created", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Registration failed: {str(e)}")

@app.post("/auth/login")
def login(credentials: UserLogin):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT id, password FROM users WHERE username = :username"),
                {"username": credentials.username}
            )
            row = result.fetchone()
            
            if not row or row[1] != credentials.password:
                raise HTTPException(401, "Invalid credentials")
            
        return {"message": "✅ Login successful", "user_id": row[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Login failed: {str(e)}")

@app.get("/dashboard")
def dashboard(token: str = Depends(security)):
    return {"message": "✅ Dashboard PostgreSQL SQLAlchemy!", "user_authenticated": True}
