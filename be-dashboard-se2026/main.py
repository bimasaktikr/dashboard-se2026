from fastapi import FastAPI
from app import models
from app.database import engine
from app.routes import router # <-- Import router di sini
from fastapi.middleware.cors import CORSMiddleware # <-- IMPORT INI

# Jika Anda sudah di TAHAP 2, nyalakan import ini:
# from app.routes import router

# Memicu pembuatan tabel secara otomatis jika belum ada di database
models.Base.metadata.create_all(bind=engine)

# INI ADALAH VARIABEL "app" YANG DICARI OLEH UVICORN
app = FastAPI(title="Command Center SE2026 API", version="1.0.0")
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Mengizinkan semua domain/port (Bisa diganti "http://localhost:5173" nanti)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Jika Anda sudah di TAHAP 2, nyalakan baris ini:
app.include_router(router)

@app.get("/")
def root_check():
    return {"status": "Pangkalan Backend Berhasil Beroperasi!", "komandan": "Siap menerima instruksi!"}