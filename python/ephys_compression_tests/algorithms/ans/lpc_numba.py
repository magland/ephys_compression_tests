"""
Numba-accelerated implementation of linear predictive coding (LPC) model operations.
All operations work with int16 data.
"""

import numpy as np
from numba import jit, prange, njit


@njit
def _create_design_matrix_channel(data: np.ndarray, order: int, subsample_factor: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Numba-optimized design matrix creation for LPC model (single channel) with optional subsampling."""
    n = len(data)
    n_samples = (n - order + subsample_factor - 1) // subsample_factor
    X_design = np.zeros((n_samples, order))
    y_target = np.zeros(n_samples)
    
    sample_idx = 0
    for i in range(0, n - order, subsample_factor):
        for j in range(order):
            X_design[sample_idx, j] = data[i + order - j - 1]
        y_target[sample_idx] = data[i + order]
        sample_idx += 1
    
    return X_design[:sample_idx], y_target[:sample_idx]


def fit_lpc_model(data: np.ndarray, k: int, subsample_factor: int = 1,
                min_samples: int = 1000) -> tuple[np.ndarray, np.ndarray]:
    """
    Fit a linear predictive coding (LPC) model of order k to multi-channel time series data.

    Args:
        data: 2D array of shape (timepoints, channels) with dtype int16
        k: Order of the LPC model
        subsample_factor: Use every Nth sample for fitting (default: 1)
        min_samples: Minimum number of samples to use for fitting (default: 1000)
    
    Returns:
        coefficients: Array of shape (channels, k) with dtype float32
        initial_points: Array of shape (channels, k) with dtype int16 (first k samples per channel)
    """
    n_timepoints, n_channels = data.shape
    if k >= n_timepoints:
        raise ValueError(f"LPC order {k} must be less than data length {n_timepoints}")
    
    # Store initial k points for each channel
    initial_points = data[:k, :].T.copy().astype(np.int16)  # Shape: (n_channels, k)
    
    # Adjust subsample_factor if needed to ensure we have at least min_samples
    effective_subsample_factor = subsample_factor
    n_subsampled = (n_timepoints - k) // effective_subsample_factor
    if n_subsampled < min_samples:
        # Adjust subsample_factor to meet min_samples requirement
        effective_subsample_factor = max(1, (n_timepoints - k) // min_samples)
    
    # Fit LPC model for each channel separately
    coefficients = np.zeros((n_channels, k), dtype=np.float32)
    
    for ch in range(n_channels):
        # Create design matrix using numba-optimized function
        # This subsamples the target points but uses full history for predictors
        X_design, y_target = _create_design_matrix_channel(data[:, ch], k, effective_subsample_factor)
        
        # Use faster solve via normal equations: (X^T X) coeffs = X^T y
        # This is faster than lstsq for overdetermined systems
        XtX = X_design.T @ X_design
        Xty = X_design.T @ y_target
        coefficients[ch] = np.linalg.solve(XtX, Xty).astype(np.float32)
    
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
                predicted += coef[i] * np.float32(data[t - 1 - i, ch])
            
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
                predicted += coef[i] * np.float32(reconstructed[t - 1 - i, ch])
            
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
    Compute residuals given data and LPC model coefficients.
    
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
                predicted += coef[i] * np.float32(reconstructed[t - 1 - i, ch])
            
            # Reconstruct: actual = predicted (rounded) + residual
            reconstructed[t, ch] = np.int16(np.round(predicted)) + residuals[t, ch]
    
    return reconstructed


def reconstruct_from_residuals(residuals: np.ndarray, coefficients: np.ndarray,
                               initial_points: np.ndarray) -> np.ndarray:
    """
    Reconstruct original data from residuals and LPC model coefficients.
    
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
        k: LPC model order for warmup
    """
    print("Warming up JIT...", end="", flush=True)
    # Create small warmup data
    warmup_data = np.random.randint(-1000, 1000, size=(1000, n_channels), dtype=np.int16)
    
    # Warm up fit_lpc_model
    coefficients, initial_points = fit_lpc_model(warmup_data, k)
    
    # Warm up compute_residuals
    residuals = compute_residuals(warmup_data, coefficients, initial_points)
    
    # Warm up compute_residuals_lossy
    _ = compute_residuals_lossy(warmup_data, coefficients, initial_points, step=2)
    
    # Warm up reconstruct_from_residuals
    _ = reconstruct_from_residuals(residuals, coefficients, initial_points)

    print(" done")
