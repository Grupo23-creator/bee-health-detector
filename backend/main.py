from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import shutil
import os
import uuid
import subprocess

from audio_processing import extract_features
from model import predict

app = FastAPI(title="Bee Health Detector")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carpeta uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Servir frontend
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")

@app.post("/predict-audio")
async def predict_audio(file: UploadFile = File(...)):

    raw_path = os.path.join(
        UPLOAD_DIR,
        f"{uuid.uuid4()}.webm"
    )

    wav_path = raw_path.replace(".webm", ".wav")

    # Guardar audio original
    with open(raw_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Convertir a WAV
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", raw_path,
            "-ar", "16000",
            "-ac", "1",
            wav_path
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    # Extraer características
    features = extract_features(wav_path)

    # Predicción
    prediction = predict(features)

    # Limpiar archivos
    os.remove(raw_path)
    os.remove(wav_path)

    result = "Healthy" if prediction == 0 else "Unhealthy"

    return {
        "prediction": result
    }