from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import subprocess
import uuid

from audio_processing import extract_features
from model import predict

app = FastAPI(title="Bee Health Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/predict-audio")
async def predict_audio(file: UploadFile = File(...)):
    # Archivos temporales
    raw_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.webm")
    wav_path = raw_path.replace(".webm", ".wav")

    # Guardar audio recibido
    with open(raw_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Convertir a WAV con ffmpeg
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

    # Extraer features y predecir
    features = extract_features(wav_path)
    prediction = predict(features)

    # Limpiar archivos
    os.remove(raw_path)
    os.remove(wav_path)

    return {
        "prediction": "Healthy" if prediction == 0 else "Unhealthy"
    }
