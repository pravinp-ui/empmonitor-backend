from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import os

app = FastAPI()

# Allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Database config (from Render environment variables)
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "port": int(os.getenv("MYSQL_PORT", 3306))
}

# Data models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# Database connection
def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(500, f"DB Error: {str(e)}")

@app.get("/")
def root():
    return {"message": "🚀 Employee Monitor API LIVE 🚀"}

@app.get("/health")
def health():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "OK", "database": "✅ CONNECTED"}
    except:
        return {"status": "Server OK", "database": "❌ Not connected"}

@app.post("/auth/register")
def register(user: UserRegister):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                      (user.username, user.email))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(400, "User already exists")
        
        # Insert user
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
        cursor.execute(
            "SELECT id, username, password FROM users WHERE username = %s",
            (credentials.username,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result or result[2] != credentials.password:
            raise HTTPException(401, "Invalid credentials")
        
        return {"message": "✅ Login successful", "user_id": result[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Login failed: {str(e)}")

@app.get("/dashboard")
def dashboard(token: str = Depends(security)):
    return {"message": "✅ Dashboard data", "user_authenticated": True}