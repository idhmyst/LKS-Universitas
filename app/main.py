from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import os

from app.schemas import QueryRequest, QueryResponse
from app.nl2sql import process_nl2sql

app = FastAPI(
    title="LKS Universitas AI API",
    description="Backend API untuk Chatbot & NL2SQL Universitas LKS",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
index_html_path = os.path.join(frontend_path, "index.html")

# Route untuk UI
@app.get("/ui", include_in_schema=False)
@app.get("/ui/", include_in_schema=False)
def serve_ui():
    if not os.path.exists(index_html_path):
        raise HTTPException(status_code=404, detail="File frontend/index.html tidak ditemukan")
    return FileResponse(index_html_path)

# Static files mount jika ada asset tambahan
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "API LKS Universitas aktif",
        "ui_url": "/ui/",
        "docs_url": "/docs"
    }

@app.post("/api/query", response_model=QueryResponse)
def handle_query(payload: QueryRequest):
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="Pertanyaan tidak boleh kosong")
    
    result = process_nl2sql(payload.question)
    return result
