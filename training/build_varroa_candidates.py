from pathlib import Path
from datetime import datetime, timezone
import re
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(r"C:\bee-health-detector")

AUDIO_DIR = BASE_DIR / "audio_2022_chunk_1"

METADATA_FILE = (
    BASE_DIR
    / "training"
    / "data"
    / "metadata"
    / "inspections_2022.csv"
)

OUTPUT_DIR = BASE_DIR / "training" / "data"

OUTPUT_FILE = OUTPUT_DIR / "varroa_candidates.csv"

# Colmenas seleccionadas para el piloto
TARGET_HIVES = {
    "3628",
    "3691",
    "3693",
}

# Umbral definido previamente:
# < 3  = Varroa baja
# >= 3 = Varroa alta
VARROA_THRESHOLD = 3.0

# Ventana máxima entre audio e inspección.
#
# Importante:
# No estamos diciendo que toda una semana tenga la misma etiqueta.
# Solo aceptamos audios relativamente cercanos a una medición.
MAX_TIME_DELTA_HOURS = 48


# ============================================================
# FUNCIONES
# ============================================================

def normalize_hive(value):
    """
    Convierte diferentes formatos de identificación
    de colmena a un identificador limpio.

    Ejemplos:
        3628       -> 3628
        HIVE-3628  -> 3628
    """
    text = str(value).strip()

    match = re.search(r"(\d+)", text)

    if match:
        return match.group(1)

    return text


def parse_audio_filename(filename):
    """
    Extrae fecha, hora y HIVE desde nombres como:

    24-08-2022_03h15_HIVE-3631.wav
    """

    pattern = (
        r"(?P<date>\d{2}-\d{2}-\d{4})_"
        r"(?P<hour>\d{2})h(?P<minute>\d{2})_"
        r"HIVE-(?P<hive>\d+)"
    )

    match = re.search(pattern, filename)

    if not match:
        return None

    date_text = match.group("date")
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    hive = match.group("hive")

    try:
        audio_datetime = datetime.strptime(
            f"{date_text} {hour:02d}:{minute:02d}",
            "%d-%m-%Y %H:%M"
        )
    except ValueError:
        return None

    return {
        "audio_date": audio_datetime.date().isoformat(),
        "audio_time": audio_datetime.strftime("%H:%M"),
        "audio_datetime": audio_datetime,
        "hive_id": hive,
    }


def load_varroa_measurements():
    """
    Lee inspections_2022.csv y conserva únicamente
    las filas Category = varroa.
    """

    print("=" * 80)
    print("CARGANDO INSPECCIONES DE VARROA")
    print("=" * 80)

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"No existe el archivo:\n{METADATA_FILE}"
        )

    df = pd.read_csv(METADATA_FILE)

    # Normalizar nombres de columnas
    df.columns = [str(c).strip() for c in df.columns]

    required_columns = [
        "Date",
        "Tag number",
        "Category",
        "Action detail",
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(
                f"No se encontró la columna requerida: {column}"
            )

    # Solo registros de Varroa
    varroa = df[
        df["Category"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("varroa")
    ].copy()

    # Identificador de colmena
    varroa["hive_id"] = (
        varroa["Tag number"]
        .apply(normalize_hive)
    )

    # Solo las tres colmenas seleccionadas
    varroa = varroa[
        varroa["hive_id"].isin(TARGET_HIVES)
    ].copy()

    # Fecha/hora de inspección
    varroa["inspection_datetime"] = pd.to_datetime(
        varroa["Date"],
        utc=True,
        errors="coerce"
    )

    # Medición numérica
    varroa["varroa_measurement"] = pd.to_numeric(
        varroa["Action detail"],
        errors="coerce"
    )

    varroa = varroa.dropna(
        subset=[
            "inspection_datetime",
            "varroa_measurement",
        ]
    )

    varroa["varroa_label"] = varroa[
        "varroa_measurement"
    ].apply(
        lambda x: "HIGH"
        if x >= VARROA_THRESHOLD
        else "LOW"
    )

    print()
    print("Mediciones seleccionadas:")
    print()

    print(
        varroa[
            [
                "inspection_datetime",
                "hive_id",
                "varroa_measurement",
                "varroa_label",
            ]
        ]
        .sort_values(["hive_id", "inspection_datetime"])
        .to_string(index=False)
    )

    print()

    return varroa


def find_audio_files():
    """
    Busca todos los WAV del chunk 1 correspondientes
    a las tres colmenas.
    """

    print("=" * 80)
    print("BUSCANDO AUDIOS")
    print("=" * 80)

    if not AUDIO_DIR.exists():
        raise FileNotFoundError(
            f"No existe la carpeta:\n{AUDIO_DIR}"
        )

    audio_files = list(
        AUDIO_DIR.rglob("*.wav")
    )

    print(f"WAV encontrados en el chunk: {len(audio_files)}")

    candidates = []

    for file_path in audio_files:

        parsed = parse_audio_filename(
            file_path.name
        )

        if parsed is None:
            continue

        if parsed["hive_id"] not in TARGET_HIVES:
            continue

        candidates.append(
            {
                "audio_file": file_path.name,
                "audio_path": str(file_path),
                "hive_id": parsed["hive_id"],
                "audio_date": parsed["audio_date"],
                "audio_time": parsed["audio_time"],
                "audio_datetime": parsed["audio_datetime"],
                "file_size_bytes": file_path.stat().st_size,
            }
        )

    print(
        f"Audios de las colmenas seleccionadas: "
        f"{len(candidates)}"
    )

    return candidates


def associate_audio_with_varroa(
    audio_files,
    varroa_df
):
    """
    Asocia cada audio con la medición de Varroa
    temporalmente más cercana de la misma colmena.

    IMPORTANTE:
    La asociación es temporal.
    No significa que el audio sea una medición directa
    de Varroa.
    """

    print("=" * 80)
    print("ASOCIANDO AUDIOS CON MEDICIONES")
    print("=" * 80)

    results = []

    for audio in audio_files:

        hive = audio["hive_id"]

        hive_measurements = varroa_df[
            varroa_df["hive_id"] == hive
        ].copy()

        if hive_measurements.empty:
            continue

        best_match = None
        best_delta = None

        for _, measurement in hive_measurements.iterrows():

            inspection_dt = measurement[
                "inspection_datetime"
            ]

            # La fecha/hora del audio no tiene timezone.
            #
            # Por ahora comparamos usando el reloj del dataset
            # y calculamos diferencia absoluta.
            #
            # La diferencia horaria entre el nombre del audio
            # y UTC debe interpretarse con cautela.
            audio_dt = audio["audio_datetime"]

            inspection_naive = (
                inspection_dt
                .tz_convert(None)
            )

            delta = abs(
                audio_dt - inspection_naive
            )

            if best_delta is None or delta < best_delta:
                best_delta = delta
                best_match = measurement

        if best_match is None:
            continue

        delta_hours = (
            best_delta.total_seconds() / 3600
        )

        # Solo aceptamos asociaciones cercanas
        if delta_hours > MAX_TIME_DELTA_HOURS:
            continue

        results.append(
            {
                "sample_id": (
                    f"{hive}_"
                    f"{audio['audio_datetime'].strftime('%Y%m%d_%H%M')}"
                ),

                "audio_file": audio["audio_file"],

                "audio_path": audio["audio_path"],

                "hive_id": hive,

                "audio_date": audio["audio_date"],

                "audio_time": audio["audio_time"],

                "audio_datetime": (
                    audio["audio_datetime"]
                    .strftime("%Y-%m-%d %H:%M:%S")
                ),

                "file_size_bytes": audio[
                    "file_size_bytes"
                ],

                "varroa_date": (
                    best_match[
                        "inspection_datetime"
                    ].strftime("%Y-%m-%d %H:%M:%S%z")
                ),

                "varroa_measurement": float(
                    best_match[
                        "varroa_measurement"
                    ]
                ),

                "varroa_label": best_match[
                    "varroa_label"
                ],

                "label_time_delta_hours": round(
                    delta_hours,
                    2
                ),

                "label_source": (
                    "UrBAN inspections_2022.csv"
                ),

                "label_status": (
                    "TEMPORAL_ASSOCIATION"
                ),

                "source_dataset": "UrBAN",
            }
        )

    return results


def main():

    print()
    print("=" * 80)
    print("BEE HEALTH DETECTOR")
    print("CONSTRUCCIÓN DE CANDIDATOS VARROA")
    print("=" * 80)
    print()

    print(f"Carpeta de audio:")
    print(AUDIO_DIR)

    print()
    print("Colmenas seleccionadas:")
    print(
        ", ".join(
            sorted(TARGET_HIVES)
        )
    )

    print()
    print(
        f"Umbral Varroa: "
        f"{VARROA_THRESHOLD}"
    )

    print(
        f"Ventana máxima: "
        f"{MAX_TIME_DELTA_HOURS} horas"
    )

    print()

    # --------------------------------------------------------
    # 1. Cargar mediciones
    # --------------------------------------------------------

    varroa_df = load_varroa_measurements()

    # --------------------------------------------------------
    # 2. Buscar audios
    # --------------------------------------------------------

    audio_files = find_audio_files()

    # --------------------------------------------------------
    # 3. Asociar audios
    # --------------------------------------------------------

    results = associate_audio_with_varroa(
        audio_files,
        varroa_df
    )

    if not results:

        print()
        print("NO SE ENCONTRARON CANDIDATOS.")
        print()
        print(
            "Posibles causas:"
        )
        print(
            "- Los audios están fuera de la ventana temporal."
        )
        print(
            "- El formato de los nombres no coincide."
        )
        print(
            "- La hora del audio y la hora UTC requieren "
            "una conversión."
        )

        return

    # --------------------------------------------------------
    # 4. Crear DataFrame
    # --------------------------------------------------------

    result_df = pd.DataFrame(results)

    # Orden
    result_df = result_df.sort_values(
        [
            "hive_id",
            "varroa_label",
            "audio_datetime",
        ]
    )

    # Crear directorio
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Guardar
    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # 5. Resumen
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("RESULTADO")
    print("=" * 80)

    print()
    print(
        f"Total candidatos: "
        f"{len(result_df)}"
    )

    print()
    print("Por colmena:")
    print()

    hive_summary = (
        result_df
        .groupby(
            [
                "hive_id",
                "varroa_label",
            ]
        )
        .size()
        .unstack(
            fill_value=0
        )
    )

    print(
        hive_summary.to_string()
    )

    print()
    print("Distribución de etiquetas:")
    print()

    print(
        result_df[
            "varroa_label"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        f"Archivo generado:"
    )

    print(OUTPUT_FILE)

    print()
    print("=" * 80)
    print("PRIMERAS FILAS")
    print("=" * 80)
    print()

    columns_to_show = [
        "audio_file",
        "hive_id",
        "varroa_measurement",
        "varroa_label",
        "label_time_delta_hours",
    ]

    print(
        result_df[
            columns_to_show
        ]
        .head(30)
        .to_string(index=False)
    )

    print()
    print("=" * 80)
    print("PROCESO TERMINADO")
    print("=" * 80)


if __name__ == "__main__":
    main()