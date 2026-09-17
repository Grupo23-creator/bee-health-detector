from pathlib import Path
import sys

import numpy as np
import pandas as pd
import librosa


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(r"C:\bee-health-detector")

MANIFEST_FILE = (
    BASE_DIR
    / "training"
    / "data"
    / "varroa_candidates.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "training"
    / "data"
    / "features.csv"
)

# Parámetros de audio
SAMPLE_RATE = 16000
SEGMENT_DURATION = 2.0

# MFCC
N_MFCC = 13
N_FFT = 1024
HOP_LENGTH = 512

# Ventana de análisis
WINDOW_TYPE = "hann"


# ============================================================
# FUNCIONES
# ============================================================

def extract_mfcc_features(audio, sr):
    """
    Extrae 13 MFCC y calcula estadísticas de cada coeficiente.

    Para cada MFCC se calculan:
        mean
        std

    Resultado:
        13 x 2 = 26 características
    """

    # Aplicar ventana Hann
    window = np.hanning(len(audio))

    audio_windowed = audio * window

    mfcc = librosa.feature.mfcc(
        y=audio_windowed,
        sr=sr,
        n_mfcc=N_MFCC,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH
    )

    features = {}

    for i in range(N_MFCC):

        coefficient = mfcc[i]

        features[f"mfcc_{i+1}_mean"] = float(
            np.mean(coefficient)
        )

        features[f"mfcc_{i+1}_std"] = float(
            np.std(coefficient)
        )

    return features


def process_audio(audio_path):
    """
    Procesa un WAV completo y lo divide en segmentos de 2 segundos.

    Devuelve una lista de características.
    """

    print()
    print("-" * 80)
    print(f"Procesando: {audio_path.name}")
    print("-" * 80)

    try:

        audio, sr = librosa.load(
            str(audio_path),
            sr=SAMPLE_RATE,
            mono=True
        )

    except Exception as e:

        print(
            f"ERROR leyendo {audio_path}: {e}"
        )

        return []

    duration = len(audio) / sr

    print(
        f"Sample rate: {sr} Hz"
    )

    print(
        f"Duración: {duration:.2f} segundos"
    )

    segment_samples = int(
        SEGMENT_DURATION * sr
    )

    total_segments = (
        len(audio) // segment_samples
    )

    print(
        f"Segmentos de {SEGMENT_DURATION:.0f} s: "
        f"{total_segments}"
    )

    results = []

    for segment_index in range(total_segments):

        start_sample = (
            segment_index * segment_samples
        )

        end_sample = (
            start_sample + segment_samples
        )

        segment = audio[
            start_sample:end_sample
        ]

        # Evitar segmentos silenciosos
        rms = np.sqrt(
            np.mean(
                np.square(segment)
            )
        )

        if rms < 1e-6:
            continue

        features = extract_mfcc_features(
            segment,
            sr
        )

        features[
            "segment_index"
        ] = segment_index

        features[
            "segment_start_sec"
        ] = segment_index * SEGMENT_DURATION

        features[
            "segment_end_sec"
        ] = (
            (segment_index + 1)
            * SEGMENT_DURATION
        )

        results.append(features)

    print(
        f"Segmentos válidos: {len(results)}"
    )

    return results


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("BEE HEALTH DETECTOR")
    print("EXTRACCIÓN DE CARACTERÍSTICAS MFCC")
    print("=" * 80)
    print()

    # --------------------------------------------------------
    # Verificar manifest
    # --------------------------------------------------------

    if not MANIFEST_FILE.exists():

        print(
            "ERROR:"
        )

        print(
            f"No existe:\n{MANIFEST_FILE}"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Leer manifest
    # --------------------------------------------------------

    df = pd.read_csv(
        MANIFEST_FILE
    )

    print(
        f"Registros encontrados en manifest: "
        f"{len(df)}"
    )

    print()

    required_columns = [
        "sample_id",
        "audio_file",
        "audio_path",
        "hive_id",
        "varroa_measurement",
        "varroa_label",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        print(
            "ERROR: faltan columnas:"
        )

        for column in missing:
            print(
                f"  - {column}"
            )

        sys.exit(1)

    # --------------------------------------------------------
    # Procesar archivos
    # --------------------------------------------------------

    all_features = []

    for _, row in df.iterrows():

        audio_path = Path(
            row["audio_path"]
        )

        if not audio_path.exists():

            print()
            print(
                f"ADVERTENCIA: no existe:"
            )

            print(audio_path)

            continue

        segments = process_audio(
            audio_path
        )

        for segment_features in segments:

            record = {
                "sample_id": row[
                    "sample_id"
                ],

                "audio_file": row[
                    "audio_file"
                ],

                "hive_id": row[
                    "hive_id"
                ],

                "varroa_measurement": row[
                    "varroa_measurement"
                ],

                "varroa_label": row[
                    "varroa_label"
                ],
            }

            record.update(
                segment_features
            )

            all_features.append(
                record
            )

    # --------------------------------------------------------
    # Verificar resultado
    # --------------------------------------------------------

    if not all_features:

        print()
        print(
            "ERROR:"
        )

        print(
            "No se pudieron generar características."
        )

        sys.exit(1)

    features_df = pd.DataFrame(
        all_features
    )

    # --------------------------------------------------------
    # Ordenar columnas
    # --------------------------------------------------------

    base_columns = [
        "sample_id",
        "audio_file",
        "hive_id",
        "varroa_measurement",
        "varroa_label",
        "segment_index",
        "segment_start_sec",
        "segment_end_sec",
    ]

    mfcc_columns = [
        column
        for column in features_df.columns
        if column.startswith("mfcc_")
    ]

    features_df = features_df[
        base_columns + mfcc_columns
    ]

    # --------------------------------------------------------
    # Guardar
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    features_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # Resumen
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("EXTRACCIÓN TERMINADA")
    print("=" * 80)

    print()

    print(
        f"Total de segmentos: "
        f"{len(features_df)}"
    )

    print()

    print("Segmentos por grabación:")

    print(
        features_df[
            [
                "audio_file",
                "hive_id",
                "varroa_label",
            ]
        ]
        .groupby(
            [
                "audio_file",
                "hive_id",
                "varroa_label",
            ]
        )
        .size()
        .to_string()
    )

    print()

    print("Distribución de etiquetas:")

    print(
        features_df[
            "varroa_label"
        ]
        .value_counts()
        .to_string()
    )

    print()

    print(
        f"Características MFCC: "
        f"{len(mfcc_columns)}"
    )

    print()

    print(
        "Archivo generado:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()