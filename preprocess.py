import numpy as np
from scipy import signal


def bandpass_filter(data, fs, low, high, order=4):
    data = np.asarray(data, dtype=float)
    nyq = 0.5 * fs
    b, a = signal.butter(order, [low / nyq, high / nyq], btype="band")
    return signal.filtfilt(b, a, data, axis=0)


def notch_filter(data, fs, freq=50.0, q=30.0):
    data = np.asarray(data, dtype=float)
    b, a = signal.iirnotch(freq, q, fs)
    return signal.filtfilt(b, a, data, axis=0)


def zscore_normalize(data, eps=1e-8):
    data = np.asarray(data, dtype=float)
    mean = np.mean(data, axis=0, keepdims=True)
    std = np.std(data, axis=0, keepdims=True)
    return (data - mean) / (std + eps)
