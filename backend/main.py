from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

import os
import shutil
import subprocess
import tempfile

import joblib
import librosa
import numpy as np
import psycopg2


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

APP_TITLE = "Bee Health Detector API"
APP_VERSION = "2.0.0"

SAMPLE_RATE = 16000
SEGMENT_DURATION = 2
SEGMENT_SAMPLES = SAMPLE_RATE * SEGMENT_DURATION

N_MFCC = 13
N_FFT = 1024
HOP_LENGTH = 512

RMS_THRESHOLD = 1e-6

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")


# =============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    """
    Crea una conexión con PostgreSQL/Supabase utilizando
    la variable de entorno DATABASE_URL.
    """

    if not DATABASE_URL:
        raise RuntimeError(
            "La variable de entorno DATABASE_URL no está configurada."
        )

    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require"
    )


# =============================================================================
# MODELO DE DATOS PARA GUARDAR ANÁLISIS
# =============================================================================

class AnalysisPayload(BaseModel):

    timestamp: Optional[str] = None

    filename: str

    hive: Optional[str] = None

    result: Optional[str] = None

    confidence: Optional[float] = 0

    totalSegments: Optional[int] = 0

    lowSegments: Optional[int] = 0

    highSegments: Optional[int] = 0

    diagnosis: Optional[str] = ""

    samplingRate: Optional[str] = ""

    segmentDuration: Optional[str] = ""

    window: Optional[str] = ""

    mfccCoefficients: Optional[int] = 0

    probabilities: Optional[Dict[str, float]] = None


# =============================================================================
# RUTA DE FFMPEG
# =============================================================================

# Detectar FFmpeg automáticamente según el entorno

if os.name == "nt":

    # Windows
    WINDOWS_FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"

    if os.path.exists(WINDOWS_FFMPEG):
        FFMPEG_PATH = WINDOWS_FFMPEG
    else:
        FFMPEG_PATH = shutil.which("ffmpeg")

else:

    # Linux / Render
    FFMPEG_PATH = shutil.which("ffmpeg")


if not FFMPEG_PATH:

    raise RuntimeError(
        "FFmpeg no está instalado o no se encuentra disponible."
    )


# =============================================================================
# APLICACIÓN FASTAPI
# =============================================================================

app = FastAPI(
    title=APP_TITLE,
    description=(
        "API para la detección bioacústica experimental "
        "de niveles asociados a Varroa destructor."
    ),
    version=APP_VERSION
)


# =============================================================================
# CORS
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# CARGAR MODELO
# =============================================================================

model = None

if os.path.exists(MODEL_PATH):

    try:

        model = joblib.load(MODEL_PATH)

        print("=" * 80)
        print("MODELO CARGADO CORRECTAMENTE")
        print("=" * 80)
        print(f"Ruta: {MODEL_PATH}")
        print(f"Tipo: {type(model).__name__}")
        print("=" * 80)

    except Exception as e:

        print("=" * 80)
        print("ERROR CARGANDO MODELO")
        print("=" * 80)
        print(str(e))
        print("=" * 80)

else:

    print("=" * 80)
    print("ADVERTENCIA")
    print("=" * 80)
    print("No se encontró el modelo:")
    print(MODEL_PATH)
    print("=" * 80)


# =============================================================================
# FUNCIONES DE AUDIO
# =============================================================================

def convert_to_wav(input_path, output_path):
    """
    Convierte el archivo recibido a WAV:

        - 16 kHz
        - mono
        - PCM 16-bit

    Utiliza FFmpeg.
    """

    if not os.path.exists(FFMPEG_PATH):

        raise RuntimeError(
            f"No se encontró FFmpeg en: {FFMPEG_PATH}"
        )

    command = [
        FFMPEG_PATH,
        "-y",
        "-i",
        input_path,
        "-ar",
        str(SAMPLE_RATE),
        "-ac",
        "1",
        "-sample_fmt",
        "s16",
        output_path
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg no pudo convertir el audio.\n"
            + result.stderr[-2000:]
        )


def extract_features_from_segment(segment):
    """
    Extrae exactamente las mismas 26 características
    utilizadas durante el entrenamiento:

        13 medias MFCC
        +
        13 desviaciones estándar MFCC

    Antes de calcular los MFCC se aplica una ventana Hann.
    """

    # Ventana Hann
    window = np.hanning(len(segment))

    windowed_segment = segment * window

    # MFCC
    mfcc = librosa.feature.mfcc(
        y=windowed_segment,
        sr=SAMPLE_RATE,
        n_mfcc=N_MFCC,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH
    )

    # Media de cada coeficiente
    mfcc_mean = np.mean(
        mfcc,
        axis=1
    )

    # Desviación estándar de cada coeficiente
    mfcc_std = np.std(
        mfcc,
        axis=1
    )

    # 13 + 13 = 26 características
    features = np.concatenate(
        [mfcc_mean, mfcc_std]
    )

    return features


def extract_audio_segments(audio_path):
    """
    Carga el audio a 16 kHz mono y lo divide en segmentos
    de exactamente 2 segundos.
    """

    audio, sr = librosa.load(
        audio_path,
        sr=SAMPLE_RATE,
        mono=True
    )

    if len(audio) < SEGMENT_SAMPLES:

        raise ValueError(
            "El audio debe tener al menos 2 segundos."
        )

    segments = []

    total_samples = len(audio)

    for start in range(
        0,
        total_samples - SEGMENT_SAMPLES + 1,
        SEGMENT_SAMPLES
    ):

        end = start + SEGMENT_SAMPLES

        segment = audio[start:end]

        # Evitar segmentos prácticamente silenciosos
        rms = np.sqrt(
            np.mean(
                np.square(segment)
            )
        )

        if rms < RMS_THRESHOLD:
            continue

        segments.append(segment)

    return segments, sr, len(audio)


def extract_features_from_audio(audio_path):
    """
    Procesa todo el audio y devuelve las características
    de cada segmento válido.
    """

    segments, sr, total_samples = extract_audio_segments(
        audio_path
    )

    if not segments:

        raise ValueError(
            "No se encontraron segmentos de audio válidos."
        )

    features_list = []

    for segment in segments:

        features = extract_features_from_segment(
            segment
        )

        features_list.append(features)

    return (
        np.array(features_list),
        sr,
        total_samples,
        len(segments)
    )


# =============================================================================
# AGREGACIÓN DE PREDICCIONES
# =============================================================================

def predict_audio(features_array):
    """
    Realiza una predicción para cada segmento y posteriormente
    obtiene un resultado global del audio.

    Se utiliza la probabilidad promedio de HIGH.
    """

    if model is None:

        raise RuntimeError(
            "El modelo no está cargado."
        )

    predictions = model.predict(
        features_array
    )

    probabilities = model.predict_proba(
        features_array
    )

    # Obtener posición de cada clase
    classes = list(model.classes_)

    if 1 in classes:
        high_index = classes.index(1)
    else:
        high_index = None

    if 0 in classes:
        low_index = classes.index(0)
    else:
        low_index = None

    # Probabilidad promedio de HIGH
    if high_index is not None:

        high_probability = float(
            np.mean(
                probabilities[:, high_index]
            )
        )

    else:

        high_probability = 0.0

    # Probabilidad promedio de LOW
    if low_index is not None:

        low_probability = float(
            np.mean(
                probabilities[:, low_index]
            )
        )

    else:

        low_probability = 0.0

    # Resultado global
    if high_probability >= low_probability:

        final_label = "HIGH"

    else:

        final_label = "LOW"

    # Cantidad de segmentos por clase
    low_segments = int(
        np.sum(predictions == 0)
    )

    high_segments = int(
        np.sum(predictions == 1)
    )

    total_segments = len(predictions)

    return {
        "label": final_label,
        "high_probability": high_probability,
        "low_probability": low_probability,
        "low_segments": low_segments,
        "high_segments": high_segments,
        "total_segments": total_segments
    }


# =============================================================================
# ENDPOINT PRINCIPAL
# =============================================================================

@app.get("/")
def read_root():

    return {
        "message": "Bee Health Detector API activa",
        "version": APP_VERSION,
        "model_loaded": model is not None,
        "database_configured": bool(DATABASE_URL),
        "sample_rate": SAMPLE_RATE,
        "segment_duration_seconds": SEGMENT_DURATION,
        "features": 26
    }


# =============================================================================
# ENDPOINT DE PREDICCIÓN
# =============================================================================

@app.post("/api/v1/predict")
async def predict_hive_health(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No se recibió ningún archivo."
        )

    # Permitimos formatos habituales de grabación
    allowed_extensions = (
        ".wav",
        ".webm",
        ".mp3",
        ".ogg",
        ".m4a"
    )

    filename_lower = file.filename.lower()

    if not filename_lower.endswith(
        allowed_extensions
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Formato de audio no compatible. "
                "Use WAV, WEBM, MP3, OGG o M4A."
            )
        )

    if model is None:

        raise HTTPException(
            status_code=500,
            detail=(
                "El modelo de detección no está disponible."
            )
        )

    # Crear archivos temporales
    input_suffix = os.path.splitext(
        file.filename
    )[1]

    input_temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=input_suffix
    )

    input_path = input_temp.name

    input_temp.close()

    wav_temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".wav"
    )

    wav_path = wav_temp.name

    wav_temp.close()

    try:

        # ---------------------------------------------------------
        # GUARDAR ARCHIVO RECIBIDO
        # ---------------------------------------------------------

        with open(
            input_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        print()
        print("=" * 80)
        print("NUEVA PREDICCIÓN")
        print("=" * 80)
        print(
            f"Archivo recibido: {file.filename}"
        )

        # ---------------------------------------------------------
        # CONVERTIR A WAV 16 kHz MONO
        # ---------------------------------------------------------

        convert_to_wav(
            input_path,
            wav_path
        )

        print(
            "Conversión: 16 kHz / mono / WAV"
        )

        # ---------------------------------------------------------
        # EXTRAER CARACTERÍSTICAS
        # ---------------------------------------------------------

        (
            features_array,
            sr,
            total_samples,
            segment_count
        ) = extract_features_from_audio(
            wav_path
        )

        duration_seconds = (
            total_samples / sr
        )

        print(
            f"Duración: {duration_seconds:.2f} segundos"
        )

        print(
            f"Segmentos válidos: {segment_count}"
        )

        print(
            f"Características por segmento: "
            f"{features_array.shape[1]}"
        )

        # ---------------------------------------------------------
        # PREDICCIÓN
        # ---------------------------------------------------------

        result = predict_audio(
            features_array
        )

        final_label = result["label"]

        high_probability = result[
            "high_probability"
        ]

        low_probability = result[
            "low_probability"
        ]

        # ---------------------------------------------------------
        # DIAGNÓSTICO PARA LA INTERFAZ
        # ---------------------------------------------------------

        if final_label == "HIGH":

            diagnosis = (
                "Nivel alto de señal asociada "
                "a Varroa destructor"
            )

            confidence = high_probability

        else:

            diagnosis = (
                "Nivel bajo de señal asociada "
                "a Varroa destructor"
            )

            confidence = low_probability

        print(
            f"Resultado: {final_label}"
        )

        print(
            f"Probabilidad HIGH: "
            f"{high_probability * 100:.2f}%"
        )

        print(
            f"Probabilidad LOW: "
            f"{low_probability * 100:.2f}%"
        )

        print("=" * 80)

        # ---------------------------------------------------------
        # RESPUESTA JSON
        # ---------------------------------------------------------

        return {

            "status": "success",

            "filename": file.filename,

            "diagnosis": diagnosis,

            "varroa_level": final_label,

            "confidence_percentage": round(
                confidence * 100,
                2
            ),

            "probabilities": {

                "LOW": round(
                    low_probability * 100,
                    2
                ),

                "HIGH": round(
                    high_probability * 100,
                    2
                )
            },

            "segments": {

                "total": result[
                    "total_segments"
                ],

                "LOW": result[
                    "low_segments"
                ],

                "HIGH": result[
                    "high_segments"
                ]
            },

            "audio_specs": {

                "sampling_rate": "16000 Hz",

                "channels": 1,

                "segment_duration": "2.0 seconds",

                "window": "Hann",

                "mfcc_coefficients": 13,

                "features_per_segment": 26
            },

            "notice": (
                "Resultado experimental del prototipo. "
                "No constituye un diagnóstico veterinario."
            )
        }

    except Exception as e:

        print()
        print(
            "ERROR DURANTE LA PREDICCIÓN:"
        )

        print(str(e))

        raise HTTPException(
            status_code=500,
            detail=(
                "Error durante el procesamiento "
                f"del audio: {str(e)}"
            )
        )

    finally:

        # Eliminar temporales
        for path in [
            input_path,
            wav_path
        ]:

            if os.path.exists(path):

                try:

                    os.remove(path)

                except Exception:

                    pass


# =============================================================================
# ENDPOINT PARA GUARDAR ANÁLISIS
# =============================================================================

@app.post("/api/v1/analyses")
def save_analysis(
    analysis: AnalysisPayload
):
    """
    Guarda un análisis realizado por el sistema
    en PostgreSQL/Supabase.
    """

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        probabilities = analysis.probabilities or {}

        low_probability = float(
            probabilities.get("LOW", 0)
        )

        high_probability = float(
            probabilities.get("HIGH", 0)
        )

        insert_query = """
            INSERT INTO public.analyses (
                filename,
                hive,
                result,
                confidence,
                total_segments,
                low_segments,
                high_segments,
                diagnosis,
                sampling_rate,
                segment_duration,
                audio_window,
                mfcc_coefficients,
                low_probability,
                high_probability
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id, created_at
        """

        cursor.execute(
            insert_query,
            (
                analysis.filename,
                analysis.hive,
                analysis.result,
                analysis.confidence,
                analysis.totalSegments,
                analysis.lowSegments,
                analysis.highSegments,
                analysis.diagnosis,
                analysis.samplingRate,
                analysis.segmentDuration,
                analysis.window,
                analysis.mfccCoefficients,
                low_probability,
                high_probability
            )
        )

        row = cursor.fetchone()

        connection.commit()

        print()
        print("=" * 80)
        print("ANÁLISIS GUARDADO EN SUPABASE")
        print("=" * 80)
        print(f"ID: {row[0]}")
        print(f"Archivo: {analysis.filename}")
        print(f"Colmena: {analysis.hive}")
        print(f"Resultado: {analysis.result}")
        print("=" * 80)

        return {
            "status": "success",
            "message": "Análisis guardado correctamente.",
            "id": str(row[0]),
            "created_at": row[1].isoformat()
        }

    except Exception as e:

        if connection:
            connection.rollback()

        print()
        print("=" * 80)
        print("ERROR GUARDANDO ANÁLISIS")
        print("=" * 80)
        print(str(e))
        print("=" * 80)

        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible guardar el análisis "
                f"en la base de datos: {str(e)}"
            )
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =============================================================================
# ENDPOINT PARA CONSULTAR HISTORIAL
# =============================================================================

@app.get("/api/v1/analyses")
def get_analyses():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            SELECT
                id,
                created_at,
                filename,
                hive,
                result,
                confidence,
                total_segments,
                low_segments,
                high_segments,
                diagnosis,
                sampling_rate,
                segment_duration,
                audio_window,
                mfcc_coefficients,
                low_probability,
                high_probability
            FROM public.analyses
            ORDER BY created_at DESC
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        analyses = []

        for row in rows:

            analyses.append({

                "id": str(row[0]),

                "timestamp": (
                    row[1].isoformat()
                    if row[1]
                    else None
                ),

                "filename": row[2],

                "hive": row[3],

                "result": row[4],

                "confidence": (
                    float(row[5])
                    if row[5] is not None
                    else 0
                ),

                "totalSegments": (
                    int(row[6])
                    if row[6] is not None
                    else 0
                ),

                "lowSegments": (
                    int(row[7])
                    if row[7] is not None
                    else 0
                ),

                "highSegments": (
                    int(row[8])
                    if row[8] is not None
                    else 0
                ),

                "diagnosis": row[9] or "",

                "samplingRate": row[10] or "",

                "segmentDuration": row[11] or "",

                "window": row[12] or "",

                "mfccCoefficients": (
                    int(row[13])
                    if row[13] is not None
                    else 0
                ),

                "probabilities": {

                    "LOW": (
                        float(row[14])
                        if row[14] is not None
                        else 0
                    ),

                    "HIGH": (
                        float(row[15])
                        if row[15] is not None
                        else 0
                    )
                }
            })

        return {
            "status": "success",
            "count": len(analyses),
            "analyses": analyses
        }

    except Exception as e:

        print()
        print("=" * 80)
        print("ERROR CONSULTANDO ANÁLISIS")
        print("=" * 80)
        print(str(e))
        print("=" * 80)

        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible consultar "
                f"los análisis: {str(e)}"
            )
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
# =============================================================================
# PRUEBA DE CONEXIÓN A BASE DE DATOS
# =============================================================================

@app.get("/database-test")
def database_test():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute("SELECT NOW();")

        row = cursor.fetchone()

        return {
            "status": "success",
            "database_connected": True,
            "database_time": row[0].isoformat()
        }

    except Exception as e:

        print()
        print("=" * 80)
        print("ERROR DE CONEXIÓN A BASE DE DATOS")
        print("=" * 80)
        print(str(e))
        print("=" * 80)

        raise HTTPException(
            status_code=500,
            detail=f"Error conectando a PostgreSQL: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()