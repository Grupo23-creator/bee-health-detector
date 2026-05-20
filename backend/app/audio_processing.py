import librosa
import numpy as np

def extract_features(file_path):
    y, sr = librosa.load(
        file_path,
        sr=16000,
        mono=True,
        duration=30,
        res_type="kaiser_fast"
    )

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfcc.T, axis=0)

    return mfcc_mean
