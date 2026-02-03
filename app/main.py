from fastapi import Request  # Add Request
from fastapi import FastAPI, HTTPException, Depends, Form, Body
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
    if not DATABASE_URL:
        raise Exception("DATABASE_URL environment variable is missing!")
    conn = None
    try:
        conn = psycopg.connect(DATABASE_URL, sslmode="require")
        yield conn
    finally:
        if conn:
            conn.close()

def create_tables():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            print("✅ Tables created!")

create_tables()

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
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "OK", "database": "✅ PostgreSQL psycopg3 CONNECTED!"}
    except Exception as e:
        return {"status": "Server OK", "database": f"❌ Error: {str(e)}"}

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

# ADD THIS FOR DESKTOP APP
@app.post("/login")
def login_universal(data: dict = {}):  # Raw dict - no validation
    """Works with username OR email"""
    username = data.get('username') or data.get('user')
    email = data.get('email') or data.get('user')
    password = data.get('password') or data.get('pass')
    
    login_field = username or email
    
    if not login_field or not password:
        return {"error": "Missing login/password"}
    
    try:
        with get_db() as conn:
            cur = conn.cursor()
            # Try username
            cur.execute("SELECT id FROM users WHERE username = %s AND password = %s", (login_field, password))
            result = cur.fetchone()
            if result:
                return {"message": "Login successful", "user_id": result[0]}
            
            # Try email
            cur.execute("SELECT id FROM users WHERE email = %s AND password = %s", (login_field, password))
            result = cur.fetchone()
            if result:
                return {"message": "Login successful", "user_id": result[0]}
                
            return {"error": "Invalid credentials"}
    except:
        return {"error": "Server error"}

@app.post("/auth/login")
def login(credentials: UserLogin):  # Keep original too
    return login_v1(credentials)

@app.get("/dashboard")
def dashboard(token: str = Depends(security)):
    return {"message": "✅ Dashboard psycopg3!", "user_authenticated": True}
