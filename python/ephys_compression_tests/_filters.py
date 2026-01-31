from typing import cast
import numpy as np
from scipy.signal import butter, lfilter


def bandpass_filter(
    array: np.ndarray, *, sampling_frequency: float, lowcut: float, highcut: float
) -> np.ndarray:
    """Apply a bandpass filter to the input array.

    Args:
        array: Input signal array
        sampling_frequency: Sampling frequency in Hz
        lowcut: Lower cutoff frequency in Hz
        highcut: Higher cutoff frequency in Hz

    Returns:
        Filtered signal array
    """
    nyquist = 0.5 * sampling_frequency
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(5, [low, high], btype="band")
    return cast(np.ndarray, lfilter(b, a, array, axis=0))


def lowpass_filter(
    array: np.ndarray, *, sampling_frequency: float, highcut: float
) -> np.ndarray:
    """Apply a lowpass filter to the input array.

    Args:
        array: Input signal array
        sampling_frequency: Sampling frequency in Hz
        highcut: Cutoff frequency in Hz

    Returns:
        Filtered signal array
    """
    nyquist = 0.5 * sampling_frequency
    high = highcut / nyquist
    b, a = butter(5, high, btype="low")
    return cast(np.ndarray, lfilter(b, a, array, axis=0))


def highpass_filter(
    array: np.ndarray, *, sampling_frequency: float, lowcut: float
) -> np.ndarray:
    """Apply a highpass filter to the input array.

    Args:
        array: Input signal array
        sampling_frequency: Sampling frequency in Hz
        lowcut: Cutoff frequency in Hz

    Returns:
        Filtered signal array
    """
    nyquist = 0.5 * sampling_frequency
    low = lowcut / nyquist
    b, a = butter(5, low, btype="high")
    return cast(np.ndarray, lfilter(b, a, array, axis=0))
