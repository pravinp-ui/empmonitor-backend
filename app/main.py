from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import os

app = FastAPI(title="Employee Monitor API")

security = HTTPBearer()

# Database config
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"), 
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "port": int(os.getenv("MYSQL_PORT", 3306))
}

# Request models
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
    except Error as e:
        raise HTTPException(500, f"DB Error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "🚀NEW_CODE_LIVE🚀", "database": "connected", "version": "v3"}


@app.post("/auth/register")
def register(user: UserRegister):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                      (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(400, "User already exists")
        
        # Insert user (password plain for demo - HASH in production!)
        cursor.execute(
            "INSERT INTO users (username, email, password, created_at) VALUES (%s, %s, %s, NOW())",
            (user.username, user.email, user.password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return {"message": "User created", "user_id": user_id}
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
        
        return {"message": "Login successful", "user_id": result[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Login failed: {str(e)}")

@app.get("/dashboard")
def dashboard(token: str = Depends(security)):
    return {"message": "Dashboard data", "user_authenticated": True}
