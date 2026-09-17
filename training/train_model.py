from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(r"C:\bee-health-detector")

FEATURES_FILE = (
    BASE_DIR
    / "training"
    / "data"
    / "features.csv"
)

MODEL_FILE = (
    BASE_DIR
    / "backend"
    / "model.pkl"
)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("BEE HEALTH DETECTOR")
    print("ENTRENAMIENTO DEL MODELO")
    print("=" * 80)
    print()

    # --------------------------------------------------------
    # 1. Cargar dataset
    # --------------------------------------------------------

    if not FEATURES_FILE.exists():

        raise FileNotFoundError(
            f"No existe:\n{FEATURES_FILE}"
        )

    df = pd.read_csv(
        FEATURES_FILE
    )

    print(
        f"Registros cargados: {len(df)}"
    )

    print()

    # --------------------------------------------------------
    # 2. Características MFCC
    # --------------------------------------------------------

    feature_columns = [
        column
        for column in df.columns
        if column.startswith("mfcc_")
    ]

    if not feature_columns:

        raise ValueError(
            "No se encontraron características MFCC."
        )

    print(
        f"Características encontradas: "
        f"{len(feature_columns)}"
    )

    print()

    # --------------------------------------------------------
    # 3. Mostrar distribución
    # --------------------------------------------------------

    print("Distribución:")

    print(
        df["varroa_label"]
        .value_counts()
        .to_string()
    )

    print()

    print("Grabaciones:")

    recording_summary = (
        df.groupby(
            [
                "audio_file",
                "hive_id",
                "varroa_label",
            ]
        )
        .size()
        .reset_index(
            name="segments"
        )
    )

    print(
        recording_summary.to_string(
            index=False
        )
    )

    print()

    # --------------------------------------------------------
    # 4. Preparar X / y
    # --------------------------------------------------------

    X = df[
        feature_columns
    ]

    y = (
        df["varroa_label"]
        .map(
            {
                "LOW": 0,
                "HIGH": 1,
            }
        )
    )

    if y.isna().any():

        raise ValueError(
            "Se encontraron etiquetas desconocidas."
        )

    # --------------------------------------------------------
    # 5. Modelo
    # --------------------------------------------------------
    #
    # Pipeline:
    #
    # MFCC
    #   ↓
    # StandardScaler
    #   ↓
    # RandomForest
    #
    # El scaler deja preparada la misma transformación
    # para utilizarla posteriormente desde FastAPI.
    #

    model = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler()
            ),

            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=200,
                    random_state=42,
                    class_weight="balanced",
                    n_jobs=-1
                )
            ),
        ]
    )

    print(
        "Entrenando Random Forest..."
    )

    model.fit(
        X,
        y
    )

    print(
        "Modelo entrenado correctamente."
    )

    print()

    # --------------------------------------------------------
    # 6. Evaluación descriptiva
    # --------------------------------------------------------
    #
    # IMPORTANTE:
    # Esta evaluación se hace sobre los mismos datos usados
    # para entrenamiento.
    #
    # NO representa una validación independiente.
    #

    predictions = model.predict(
        X
    )

    print("=" * 80)
    print("EVALUACIÓN SOBRE LOS DATOS DE ENTRENAMIENTO")
    print("=" * 80)

    print()

    print(
        classification_report(
            y,
            predictions,
            target_names=[
                "LOW",
                "HIGH",
            ],
            zero_division=0
        )
    )

    print(
        "Matriz de confusión:"
    )

    print(
        confusion_matrix(
            y,
            predictions
        )
    )

    print()

    # --------------------------------------------------------
    # 7. Guardar modelo
    # --------------------------------------------------------

    MODEL_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_FILE
    )

    print(
        "Modelo guardado:"
    )

    print(
        MODEL_FILE
    )

    print()

    # --------------------------------------------------------
    # 8. Información del modelo
    # --------------------------------------------------------

    print("=" * 80)
    print("RESUMEN DEL MODELO")
    print("=" * 80)

    print()

    print(
        "Clasificador: RandomForestClassifier"
    )

    print(
        "Árboles: 200"
    )

    print(
        "Características: 26 MFCC"
    )

    print(
        "Etiquetas:"
    )

    print(
        "  0 = LOW"
    )

    print(
        "  1 = HIGH"
    )

    print()

    print(
        "ADVERTENCIA:"
    )

    print(
        "La evaluación anterior es únicamente descriptiva."
    )

    print(
        "No constituye una validación independiente del modelo."
    )

    print()

    print("=" * 80)
    print("ENTRENAMIENTO TERMINADO")
    print("=" * 80)


if __name__ == "__main__":
    main()