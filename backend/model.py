import os
import joblib


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "model.pkl"
)


if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"No se encontró el modelo en: {MODEL_PATH}"
    )


model = joblib.load(MODEL_PATH)


def predict(features):
    """
    Realiza una predicción utilizando las 26 características MFCC.

    features:
        Lista o vector con 26 valores.
    """

    prediction = model.predict([features])[0]

    probabilities = None

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba([features])[0]

    return prediction, probabilities