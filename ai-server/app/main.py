from fastapi import FastAPI
from app.api.routes_chat import router as chat_router

app = FastAPI(title="AI Backend", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(chat_router, prefix="/api/v1")
