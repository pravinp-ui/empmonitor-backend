from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "🚀 Employee Monitor API LIVE 🚀"}

@app.get("/health")
def health():
    return {"status": "🚀NEW_CODE_100%_LIVE🚀", "version": "v4", "endpoints": ["/auth/register", "/auth/login"]}

@app.post("/auth/register")
def register():
    return {"message": "✅ REGISTER WORKS!", "username": "testuser", "user_id": 1}

@app.post("/auth/login") 
def login():
    return {"message": "✅ LOGIN WORKS!", "user_id": 1, "token": "demo-jwt-token"}

@app.get("/dashboard")
def dashboard():
    return {"message": "✅ DASHBOARD WORKS!", "data": "Your employee data here"}
