from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import psycopg
from contextlib import contextmanager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
DATABASE_URL = os.getenv("DATABASE_URL")

@contextmanager
def get_db():
    conn = None
    try:
        conn = psycopg.connect(DATABASE_URL, sslmode="require")
        yield conn
    finally:
        if conn:
            conn.close()

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

@app.get("/")
def root():
    return {"message": "🚀 Employee Monitor API LIVE 🚀 psycopg3 PURE!"}

@app.get("/health")
def health():
    db_status = "❌ DATABASE_URL MISSING!" if not DATABASE_URL else "✅ Found"
    try:
        if not DATABASE_URL:
            return {"status": "Server OK", "database": db_status, "DATABASE_URL": "NULL"}
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "OK", "database": "✅ PostgreSQL psycopg3 CONNECTED!", "DATABASE_URL": "OK"}
    except Exception as e:
        return {"status": "Server OK", "database": f"❌ Error: {str(e)}", "DATABASE_URL": db_status}


@app.post("/auth/register")
def register(user: UserRegister):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                           (user.username, user.email))
                if cur.fetchone():
                    raise HTTPException(400, "User exists")
                
                cur.execute(
                    "INSERT INTO users (username, email, password, created_at) VALUES (%s, %s, %s, NOW()) RETURNING id",
                    (user.username, user.email, user.password)
                )
                user_id = cur.fetchone()[0]
                conn.commit()
                
        return {"message": "✅ User created", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Registration failed: {str(e)}")

@app.post("/auth/login")
def login(credentials: UserLogin):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, password FROM users WHERE username = %s", (credentials.username,))
                result = cur.fetchone()
                
                if not result or result[1] != credentials.password:
                    raise HTTPException(401, "Invalid credentials")
                
        return {"message": "✅ Login successful", "user_id": result[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Login failed: {str(e)}")

@app.get("/dashboard")
def dashboard(token: str = Depends(security)):
    return {"message": "✅ Dashboard psycopg3!", "user_authenticated": True}
