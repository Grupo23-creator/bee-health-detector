from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import subprocess

from audio_processing import extract_features
from model import predict

# ---------------------------
# App
# ---------------------------
app = FastAPI(title="Bee Health Detector")

# ---------------------------
# CORS
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Paths
# ---------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

WEBM_PATH = os.path.join(UPLOAD_DIR, "recording.webm")
WAV_PATH = os.path.join(UPLOAD_DIR, "recording.wav")

# ---------------------------
# Endpoint
# ---------------------------
@app.post("/predict-audio")
async def predict_audio(file: UploadFile = File(...)):

    # 1️⃣ Guardar archivo webm tal cual viene del navegador
    with open(WEBM_PATH, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2️⃣ Convertir webm → wav (formato que entiende librosa)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", WEBM_PATH,
            "-ar", "16000",
            "-ac", "1",
            WAV_PATH
        ],
        check=True
    )

    # 3️⃣ Extraer features
    features = extract_features(WAV_PATH)

    # 4️⃣ Predecir
    prediction = predict(features)

    result = "Healthy" if prediction == 0 else "Unhealthy"

    return {
        "prediction": result
    }
