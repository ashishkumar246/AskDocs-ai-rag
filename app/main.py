from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.chroma_db import delete_user_upload_collections


app = FastAPI(title="AskDocs AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def clear_old_uploads():
    delete_user_upload_collections()


@app.on_event("shutdown")
def clear_uploads_on_shutdown():
    delete_user_upload_collections()


@app.get("/")
def home():
    return {"message": "AskDocs AI API Running"}
