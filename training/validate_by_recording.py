import os
import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

FEATURES_PATH = r"C:\bee-health-detector\training\data\features.csv"

RANDOM_STATE = 42


# =============================================================================
# CARGAR DATOS
# =============================================================================

print("=" * 80)
print("BEE HEALTH DETECTOR")
print("VALIDACIÓN POR GRABACIÓN")
print("=" * 80)

if not os.path.exists(FEATURES_PATH):
    raise FileNotFoundError(
        f"No se encontró: {FEATURES_PATH}"
    )

df = pd.read_csv(FEATURES_PATH)

print()
print(f"Registros cargados: {len(df)}")


# =============================================================================
# CARACTERÍSTICAS
# =============================================================================

feature_columns = [
    column
    for column in df.columns
    if column.startswith("mfcc_")
]

print(
    f"Características encontradas: "
    f"{len(feature_columns)}"
)

if len(feature_columns) != 26:
    raise ValueError(
        "Se esperaban exactamente 26 características MFCC."
    )


# =============================================================================
# INFORMACIÓN DE LAS GRABACIONES
# =============================================================================

print()
print("=" * 80)
print("GRABACIONES")
print("=" * 80)

recordings = (
    df.groupby(
        [
            "audio_file",
            "hive_id",
            "varroa_label"
        ]
    )
    .size()
    .reset_index(name="segments")
)

print(
    recordings.to_string(index=False)
)


# =============================================================================
# MODELO
# =============================================================================

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
                random_state=RANDOM_STATE,
                class_weight="balanced",
                n_jobs=-1
            )
        )
    ]
)


# =============================================================================
# VALIDACIÓN LEAVE-ONE-RECORDING-OUT
# =============================================================================

print()
print("=" * 80)
print("VALIDACIÓN LEAVE-ONE-RECORDING-OUT")
print("=" * 80)

all_results = []


for _, test_recording in recordings.iterrows():

    test_audio = test_recording["audio_file"]

    print()
    print("-" * 80)
    print(f"Grabación de prueba:")
    print(test_audio)

    # Datos de entrenamiento
    train_df = df[
        df["audio_file"] != test_audio
    ].copy()

    # Datos de prueba
    test_df = df[
        df["audio_file"] == test_audio
    ].copy()

    X_train = train_df[
        feature_columns
    ].values

    y_train = train_df[
        "varroa_label"
    ].map({
        "LOW": 0,
        "HIGH": 1
    }).values

    X_test = test_df[
        feature_columns
    ].values

    y_test = test_df[
        "varroa_label"
    ].map({
        "LOW": 0,
        "HIGH": 1
    }).values

    # Comprobar que entrenamiento tenga ambas clases
    train_classes = np.unique(y_train)

    if len(train_classes) < 2:

        print(
            "No es posible entrenar con ambas clases "
            "en este caso."
        )

        continue

    # Entrenar
    model.fit(
        X_train,
        y_train
    )

    # Predecir segmentos
    predictions = model.predict(
        X_test
    )

    probabilities = model.predict_proba(
        X_test
    )

    classes = list(
        model.classes_
    )

    high_index = classes.index(1)
    low_index = classes.index(0)

    high_probability = float(
        np.mean(
            probabilities[:, high_index]
        )
    )

    low_probability = float(
        np.mean(
            probabilities[:, low_index]
        )
    )

    final_prediction = (
        "HIGH"
        if high_probability >= low_probability
        else "LOW"
    )

    low_segments = int(
        np.sum(predictions == 0)
    )

    high_segments = int(
        np.sum(predictions == 1)
    )

    actual_label = test_recording[
        "varroa_label"
    ]

    correct = (
        final_prediction == actual_label
    )

    print()
    print(
        f"Etiqueta real:       {actual_label}"
    )

    print(
        f"Predicción global:    {final_prediction}"
    )

    print(
        f"Probabilidad LOW:     "
        f"{low_probability * 100:.2f}%"
    )

    print(
        f"Probabilidad HIGH:    "
        f"{high_probability * 100:.2f}%"
    )

    print(
        f"Segmentos LOW:        {low_segments}"
    )

    print(
        f"Segmentos HIGH:       {high_segments}"
    )

    print(
        f"Resultado correcto:   "
        f"{'SI' if correct else 'NO'}"
    )

    all_results.append({
        "audio_file": test_audio,
        "hive_id": test_recording["hive_id"],
        "real": actual_label,
        "prediccion": final_prediction,
        "prob_low": low_probability,
        "prob_high": high_probability,
        "segmentos_low": low_segments,
        "segmentos_high": high_segments,
        "correcto": correct
    })


# =============================================================================
# RESUMEN
# =============================================================================

print()
print("=" * 80)
print("RESUMEN DE VALIDACIÓN")
print("=" * 80)

if all_results:

    results_df = pd.DataFrame(
        all_results
    )

    print()
    print(
        results_df.to_string(
            index=False
        )
    )

    accuracy = (
        results_df["correcto"].mean()
    )

    print()
    print(
        f"Grabaciones evaluadas: "
        f"{len(results_df)}"
    )

    print(
        f"Grabaciones clasificadas correctamente: "
        f"{results_df['correcto'].sum()}"
    )

    print(
        f"Exactitud por grabación: "
        f"{accuracy * 100:.2f}%"
    )

else:

    print(
        "No fue posible realizar la validación."
    )


print()
print("=" * 80)
print("FIN DE LA VALIDACIÓN")
print("=" * 80)