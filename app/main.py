from fastapi import Request  # Add Request
from fastapi import FastAPI, HTTPException, Depends, Form
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
async def login_debug(request: Request):
    """DEBUG: Shows EXACT data desktop sends"""
    try:
        # Log EVERYTHING desktop sends
        print(f"🔍 RAW HEADERS: {dict(request.headers)}")
        print(f"🔍 RAW BODY: {await request.body()}")
        
        # Try ALL possible formats
        body_bytes = await request.body()
        body_text = body_bytes.decode('utf-8') if body_bytes else ""
        print(f"🔍 BODY TEXT: {body_text}")
        
        # Method 1: JSON
        try:
            body_json = await request.json()
            username = body_json.get("username", body_json.get("user"))
            password = body_json.get("password", body_json.get("pass"))
            print(f"🔍 JSON: username={username}, password={password}")
        except:
            username = password = None
            
        # Method 2: Form
        try:
            form = await request.form()
            username = form.get("username", form.get("user"))
            password = form.get("password", form.get("pass"))
            print(f"🔍 FORM: username={username}, password={password}")
        except:
            pass
            
        # Method 3: Raw parsing
        if not username and body_text:
            if "username=" in body_text:
                username = body_text.split("username=")[1].split("&")[0]
            if "password=" in body_text:
                password = body_text.split("password=")[1]
            print(f"🔍 RAW: username={username}, password={password}")
        
        print(f"🔍 FINAL: username='{username}', password='{password}'")
        
        if not username or not password:
            return {"error": "Missing credentials", "debug": {"username": username, "password": password, "body": body_text[:200]}}
        
        # Login logic
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
                result = cur.fetchone()
                
                if not result or result[1] != password:
                    return {"error": "Invalid credentials", "debug": {"username": username}}
                    
        return {"message": "Login successful", "user_id": result[0], "username": username}
        
    except Exception as e:
        return {"error": str(e), "debug": "Exception occurred"}



@app.post("/auth/login")
def login(credentials: UserLogin):  # Keep original too
    return login_v1(credentials)

@app.get("/dashboard")
def dashboard(token: str = Depends(security)):
    return {"message": "✅ Dashboard psycopg3!", "user_authenticated": True}
