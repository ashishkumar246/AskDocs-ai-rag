from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Medical RAG API")

app.include_router(router)


@app.get("/")
def home():
    return {"message": "Medical RAG API Running"}