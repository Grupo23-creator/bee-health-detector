import librosa
import numpy as np

def process_audio_sample(file_path, sr_target=8000, duration=2.0, n_mfcc=20):
    """
    Carga, resamplea a 8kHz, ajusta la duración a 2.0s y extrae vectores MFCC.
    """
    # 1. Cargar audio resampleando a 8kHz y convirtiendo a Mono
    y, sr = librosa.load(file_path, sr=sr_target, mono=True)
    
    # 2. Ajustar exactamente a 2.0 segundos (16,000 muestras a 8kHz)
    target_length = int(sr_target * duration)
    if len(y) < target_length:
        y = np.pad(y, (0, target_length - len(y)), mode='constant')
    else:
        y = y[:target_length]
        
    # 3. Extraer Coeficientes MFCC
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    
    # 4. Obtener el promedio de los coeficientes a lo largo del tiempo (Vector característico)
    mfccs_scaled = np.mean(mfccs.T, axis=0)
    
    return mfccs_scaled
