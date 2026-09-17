<<<<<<< HEAD
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
=======
import os
import glob
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
from audio_processor import process_audio_sample

# 1. Definir rutas del dataset
# Estructura esperada en tu carpeta de datos:
# dataset/
#   ├── sano/          (archivos .wav de colmenas sanas)
#   └── varroa/        (archivos .wav de colmenas infestadas)

DATASET_PATH = "./dataset" 

def load_dataset_and_extract_features(data_dir):
    X = []
    y = []
    
    classes = {"sano": 0, "varroa": 1}
    
    for class_name, label in classes.items():
        folder_path = os.path.join(data_dir, class_name)
        audio_files = glob.glob(os.path.join(folder_path, "*.wav"))
        
        print(f"Procesando {len(audio_files)} archivos de la clase: '{class_name}'...")
        
        for file_path in audio_files:
            try:
                features = process_audio_sample(file_path)
                X.append(features)
                y.append(label)
            except Exception as e:
                print(f"Error procesando {file_path}: {e}")
                
    return np.array(X), np.array(y)

def train_and_evaluate():
    print("=== INICIANDO EXTRACCIÓN DE CARACTERÍSTICAS (MFCC) ===")
    X, y = load_dataset_and_extract_features(DATASET_PATH)
    
    if len(X) == 0:
        print("ERROR: No se encontraron archivos .wav en la carpeta 'dataset/'. Verifica la ruta.")
        return

    # 2. División de datos (80% Entrenamiento, 20% Prueba)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    # 3. Entrenamiento del Modelo (Random Forest)
    print("\n=== ENTRENANDO EL CLASIFICADOR ===")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 4. Evaluación en el conjunto de prueba
    y_pred = model.predict(X_test)
    
    # 5. Cálculo de Métricas MEM-IA (Sección 7.5.1 de la plantilla)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    
    print("\n==================================================")
    print("         MÉTRICAS DE EVALUACIÓN (MEM-IA)          ")
    print("==================================================")
    print(f"Exactitud (Accuracy):  {acc * 100:.2f}%")
    print(f"Precisión (Precision): {prec * 100:.2f}%")
    print(f"Sensibilidad (Recall): {rec * 100:.2f}%")
    print(f"F1-Score:              {f1 * 100:.2f}%")
    print("\nMatriz de Confusión:")
    print(cm)
    print("==================================================\n")
    
    # 6. Guardar el modelo entrenado y las métricas
    joblib.dump(model, "varroa_detector_model.pkl")
    print("¡Modelo guardado exitosamente en 'varroa_detector_model.pkl'!")

if __name__ == "__main__":
    train_and_evaluate()
>>>>>>> origin/main
