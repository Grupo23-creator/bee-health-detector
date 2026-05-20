import pickle
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def predict(features):
    """
    features: np.array shape (40,)
    """
    return model.predict([features])[0]
