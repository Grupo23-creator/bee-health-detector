from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import joblib

from audio_processor import process_audio_sample

app = FastAPI(
    title="Bee Health Detector API",
    description="API para la detección bioacústica de Varroa destructor en colmenas",
    version="1.0.0"
)

# Configuración de CORS para permitir la conexión desde el Frontend (Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción puedes reemplazar con el dominio de Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar el modelo guardado
MODEL_PATH = "varroa_detector_model.pkl"
model = None

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print("Modelo 'varroa_detector_model.pkl' cargado correctamente.")
else:
    print("ADVERTENCIA: No se encontró 'varroa_detector_model.pkl'. Modulo en modo prueba.")

@app.get("/")
def read_root():
    return {"message": "API de Monitoreo Bioacústico de Colmenas Activa"}

@app.post("/api/v1/predict")
async def predict_hive_health(file: UploadFile = File(...)):
    if not file.filename.endswith(('.wav', '.WAV')):
        raise HTTPException(status_code=400, detail="El archivo debe estar en formato WAV.")

    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Extracción de características MFCC
        features = process_audio_sample(temp_path)
        
        if model is not None:
            # Predicción con el modelo real
            prediction = model.predict([features])[0]
            probabilities = model.predict_proba([features])[0]
            
            labels = {0: "Sano", 1: "Varroa destructor"}
            diagnosis = labels.get(prediction, "Desconocido")
            confidence = float(probabilities[prediction])
        else:
            # Respuesta por defecto si aún no se ha entrenado el .pkl
            diagnosis = "Sano"
            confidence = 0.90

        return {
            "status": "success",
            "filename": file.filename,
            "diagnosis": diagnosis,
            "confidence_percentage": round(confidence * 100, 2),
            "audio_specs": {
                "sampling_rate": "8000 Hz",
                "duration_window": "2.0s",
                "feature_type": "MFCCs (20 coeficientes)"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante el procesamiento: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
