"""
Numba-accelerated implementation of autoregressive model operations.
All operations work with int16 data.
"""

import numpy as np
from numba import jit, prange


@jit(nopython=True, parallel=False, fastmath=True)
def _fit_ar_model_channel(channel_data: np.ndarray, k: int, subsample_factor: int,
                         min_samples: int) -> np.ndarray:
    """
    Fit AR model for a single channel using least squares with subsampling.
    
    Args:
        channel_data: 1D array for a single channel (int16)
        k: AR model order
        subsample_factor: Use every Nth sample for fitting
        min_samples: Minimum number of samples to use
    
    Returns:
        coefficients: 1D array of k coefficients (float32)
    """
    n = len(channel_data)
    
    # Determine subsampling stride
    max_samples = n - k
    stride = max(1, max_samples // min_samples, subsample_factor)
    
    # Number of samples we'll actually use
    n_samples = (max_samples + stride - 1) // stride
    
    # Build design matrix X and target vector y using subsampled data
    # X has shape (n_samples, k), y has shape (n_samples,)
    X = np.zeros((n_samples, k), dtype=np.float32)
    y = np.zeros(n_samples, dtype=np.float32)
    
    sample_idx = 0
    for t in range(k, n, stride):
        if sample_idx >= n_samples:
            break
        for i in range(k):
            X[sample_idx, i] = np.float32(channel_data[t - k + i])
        y[sample_idx] = np.float32(channel_data[t])
        sample_idx += 1
    
    # Truncate if needed
    actual_samples = sample_idx
    if actual_samples < n_samples:
        X = X[:actual_samples, :]
        y = y[:actual_samples]
    
    # Solve normal equations: X.T @ X @ coef = X.T @ y
    XtX = np.zeros((k, k), dtype=np.float32)
    Xty = np.zeros(k, dtype=np.float32)
    
    for i in range(k):
        for j in range(k):
            for t in range(actual_samples):
                XtX[i, j] += X[t, i] * X[t, j]
    
    for i in range(k):
        for t in range(actual_samples):
            Xty[i] += X[t, i] * y[t]
    
    # Solve the system using numpy's solver
    coefficients = np.linalg.solve(XtX, Xty)
    
    return coefficients


def fit_ar_model(data: np.ndarray, k: int, subsample_factor: int = 100,
                min_samples: int = 1000) -> tuple[np.ndarray, np.ndarray]:
    """
    Fit an autoregressive model of order k to multi-channel time series data.
    
    Args:
        data: 2D array of shape (timepoints, channels) with dtype int16
        k: Order of the autoregressive model
        subsample_factor: Use every Nth sample for fitting (default: 100)
        min_samples: Minimum number of samples to use for fitting (default: 1000)
    
    Returns:
        coefficients: Array of shape (channels, k) with dtype float32
        initial_points: Array of shape (channels, k) with dtype int16 (first k samples per channel)
    """
    n_timepoints, n_channels = data.shape
    
    if n_timepoints <= k:
        raise ValueError(f"Need at least {k+1} timepoints for AR({k}) model")
    
    # Store initial k points for each channel
    initial_points = data[:k, :].T.copy()  # (channels, k)
    
    # Fit coefficients for each channel
    coefficients = np.zeros((n_channels, k), dtype=np.float32)
    
    for ch in range(n_channels):
        coefficients[ch, :] = _fit_ar_model_channel(data[:, ch], k, subsample_factor, min_samples)
    
    return coefficients, initial_points


@jit(nopython=True, parallel=True, fastmath=True)
def _compute_residuals_jit(data: np.ndarray, coefficients: np.ndarray, 
                           initial_points: np.ndarray, k: int) -> np.ndarray:
    """
    JIT-compiled residuals computation.
    """
    n_timepoints, n_channels = data.shape
    residuals = np.zeros((n_timepoints, n_channels), dtype=np.int16)
    
    # First k points are copied as-is
    residuals[:k, :] = initial_points.T
    
    # Compute residuals for each channel in parallel
    for ch in prange(n_channels):
        coef = coefficients[ch, :]
        
        for t in range(k, n_timepoints):
            # Predict from previous k samples
            predicted = np.float32(0.0)
            for i in range(k):
                predicted += coef[i] * np.float32(data[t - k + i, ch])
            
            # Residual = actual - predicted (rounded)
            residuals[t, ch] = data[t, ch] - np.int16(np.round(predicted))
    
    return residuals


@jit(nopython=True, parallel=True, fastmath=True)
def _compute_residuals_lossy_jit(data: np.ndarray, coefficients: np.ndarray,
                                 initial_points: np.ndarray, k: int, step: int) -> np.ndarray:
    """
    JIT-compiled lossy residuals computation with quantization feedback.
    """
    n_timepoints, n_channels = data.shape
    residuals = np.zeros((n_timepoints, n_channels), dtype=np.int16)
    reconstructed = np.zeros((n_timepoints, n_channels), dtype=np.int16)
    
    # First k points are copied as-is
    residuals[:k, :] = initial_points.T
    reconstructed[:k, :] = initial_points.T
    
    step_f32 = np.float32(step)
    
    # Compute residuals for each channel in parallel
    for ch in prange(n_channels):
        coef = coefficients[ch, :]
        
        for t in range(k, n_timepoints):
            # Predict from previous k reconstructed samples
            predicted = np.float32(0.0)
            for i in range(k):
                predicted += coef[i] * np.float32(reconstructed[t - k + i, ch])
            
            prediction_int = np.int16(np.round(predicted))
            
            # Compute residual from original data
            residual = data[t, ch] - prediction_int
            
            # Quantize residual to nearest multiple of step
            quantized_residual = np.int16(np.round(np.float32(residual) / step_f32) * step_f32)
            residuals[t, ch] = quantized_residual
            
            # Reconstruct sample using quantized residual for future predictions
            reconstructed[t, ch] = prediction_int + quantized_residual
    
    return residuals


def compute_residuals(data: np.ndarray, coefficients: np.ndarray, 
                      initial_points: np.ndarray) -> np.ndarray:
    """
    Compute residuals given data and AR model coefficients.
    
    Args:
        data: 2D array of shape (timepoints, channels) with dtype int16
        coefficients: Array of shape (channels, k) with dtype float32
        initial_points: Array of shape (channels, k) with dtype int16
    
    Returns:
        residuals: Array of shape (timepoints, channels) with dtype int16
    """
    k = coefficients.shape[1]
    return _compute_residuals_jit(data, coefficients, initial_points, k)


def compute_residuals_lossy(data: np.ndarray, coefficients: np.ndarray,
                           initial_points: np.ndarray, step: int) -> np.ndarray:
    """
    Compute lossy residuals with quantization given data and AR model coefficients.
    
    Args:
        data: 2D array of shape (timepoints, channels) with dtype int16
        coefficients: Array of shape (channels, k) with dtype float32
        initial_points: Array of shape (channels, k) with dtype int16
        step: Quantization step size
    
    Returns:
        residuals: Array of shape (timepoints, channels) with dtype int16
    """
    k = coefficients.shape[1]
    return _compute_residuals_lossy_jit(data, coefficients, initial_points, k, step)


@jit(nopython=True, parallel=True, fastmath=True)
def _reconstruct_from_residuals_jit(residuals: np.ndarray, coefficients: np.ndarray,
                                    initial_points: np.ndarray, k: int) -> np.ndarray:
    """
    JIT-compiled reconstruction.
    """
    n_timepoints, n_channels = residuals.shape
    reconstructed = np.zeros((n_timepoints, n_channels), dtype=np.int16)
    
    # First k points are copied from initial_points
    reconstructed[:k, :] = initial_points.T
    
    # Reconstruct each channel in parallel
    for ch in prange(n_channels):
        coef = coefficients[ch, :]
        
        for t in range(k, n_timepoints):
            # Predict from previous k reconstructed samples
            predicted = np.float32(0.0)
            for i in range(k):
                predicted += coef[i] * np.float32(reconstructed[t - k + i, ch])
            
            # Reconstruct: actual = predicted (rounded) + residual
            reconstructed[t, ch] = np.int16(np.round(predicted)) + residuals[t, ch]
    
    return reconstructed


def reconstruct_from_residuals(residuals: np.ndarray, coefficients: np.ndarray,
                               initial_points: np.ndarray) -> np.ndarray:
    """
    Reconstruct original data from residuals and AR model coefficients.
    
    Args:
        residuals: 2D array of shape (timepoints, channels) with dtype int16
        coefficients: Array of shape (channels, k) with dtype float32
        initial_points: Array of shape (channels, k) with dtype int16
    
    Returns:
        reconstructed: Array of shape (timepoints, channels) with dtype int16
    """
    k = coefficients.shape[1]
    return _reconstruct_from_residuals_jit(residuals, coefficients, initial_points, k)


def warmup(n_channels: int = 10, k: int = 10):
    """
    Warm up Numba JIT compilation for all functions.
    
    Args:
        n_channels: Number of channels for warmup data
        k: AR model order for warmup
    """
    print("Warming up JIT...", end="", flush=True)
    # Create small warmup data
    warmup_data = np.random.randint(-1000, 1000, size=(1000, n_channels), dtype=np.int16)
    
    # Warm up fit_ar_model
    coefficients, initial_points = fit_ar_model(warmup_data, k)
    
    # Warm up compute_residuals
    residuals = compute_residuals(warmup_data, coefficients, initial_points)
    
    # Warm up compute_residuals_lossy
    _ = compute_residuals_lossy(warmup_data, coefficients, initial_points, step=2)
    
    # Warm up reconstruct_from_residuals
    _ = reconstruct_from_residuals(residuals, coefficients, initial_points)

    print(" done")
