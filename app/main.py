from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import psycopg2

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

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

def get_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

@app.get("/")
def root():
    return {"message": "🚀 Employee Monitor API LIVE 🚀 PostgreSQL!"}

@app.get("/health")
def health():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "OK", "database": "✅ PostgreSQL CONNECTED!"}
    except Exception as e:
        return {"status": "Server OK", "database": f"❌ Error: {str(e)}"}

@app.post("/auth/register")
def register(user: UserRegister):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                      (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(400, "User exists")
        
        cursor.execute(
            "INSERT INTO users (username, email, password, created_at) VALUES (%s, %s, %s, NOW())",
            (user.username, user.email, user.password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        return {"message": "✅ User created", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Registration failed: {str(e)}")

@app.post("/auth/login")
def login(credentials: UserLogin):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (credentials.username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result or result[1] != credentials.password:
            raise HTTPException(401, "Invalid credentials")
        
        return {"message": "✅ Login successful", "user_id": result[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Login failed: {str(e)}")

@app.get("/dashboard")
def dashboard(token: str = Depends(security)):
    return {"message": "✅ Dashboard PostgreSQL!", "user_authenticated": True}
