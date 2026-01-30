"""Auto-regressive model utilities for ANS compression."""

import numpy as np
from typing import Tuple
from numba import njit


def _warmup_numba_functions():
    """Warmup numba JIT compilation with small test data."""
    print("Warming up numba functions for AR model...")
    # Create small test data for 2D arrays (timepoints x channels)
    test_data = np.array([[1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9]], dtype=np.int16)
    test_coeffs = np.array([[0.5, 0.3], [0.4, 0.2]], dtype=np.float32)  # channels x order
    test_residuals = np.array([[1, 2], [2, 3], [3, 4], [4, 5]], dtype=np.int16)
    test_initial = np.array([[1, 2], [2, 3]], dtype=np.int16)
    test_step = 2
    
    # Warmup each numba function
    _create_design_matrix_channel(test_data[:, 0], 2)
    _apply_ar_residuals_kernel_channel(test_data[:, 0], test_coeffs[0])
    _apply_ar_residuals_lossy_kernel_channel(test_data[:, 0], test_coeffs[0], test_step)
    _decode_ar_kernel_channel(test_coeffs[0], test_residuals[:, 0], test_initial[:, 0])


@njit
def _create_design_matrix_channel(data: np.ndarray, order: int) -> Tuple[np.ndarray, np.ndarray]:
    """Numba-optimized design matrix creation for AR model (single channel)."""
    n = len(data)
    X_design = np.zeros((n - order, order))
    y_target = data[order:]
    
    for i in range(n - order):
        for j in range(order):
            X_design[i, j] = data[i + order - j - 1]
    
    return X_design, y_target


def fit_ar_model(data: np.ndarray, order: int) -> np.ndarray:
    """
    Fit an autoregressive model of given order using least squares.
    
    Args:
        data: Input data array (timepoints x channels)
        order: AR model order
        
    Returns:
        AR coefficients as numpy array (channels x order)
    """
    n_timepoints, n_channels = data.shape
    if order >= n_timepoints:
        raise ValueError(f"AR order {order} must be less than data length {n_timepoints}")
    
    # Fit AR model for each channel separately
    coeffs = np.zeros((n_channels, order), dtype=np.float32)
    
    for ch in range(n_channels):
        # Create design matrix using numba-optimized function
        X_design, y_target = _create_design_matrix_channel(data[:, ch], order)
        
        # Use faster solve via normal equations: (X^T X) coeffs = X^T y
        # This is faster than lstsq for overdetermined systems
        XtX = X_design.T @ X_design
        Xty = X_design.T @ y_target
        coeffs[ch] = np.linalg.solve(XtX, Xty)
    
    return coeffs


@njit
def _apply_ar_residuals_kernel_channel(data: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    """Numba-optimized kernel for computing AR residuals (single channel)."""
    order = len(coeffs)
    n = len(data)
    residuals = np.empty(n - order, dtype=data.dtype)
    
    for i in range(order, n):
        # Predict using previous 'order' samples
        # Use float32 accumulation
        prediction = np.float32(0.0)
        for j in range(order):
            prediction += coeffs[j] * np.float32(data[i - j - 1])
        
        # Round to nearest integer using numpy's round (banker's rounding)
        prediction_int = np.int16(np.round(prediction))
        residual = data[i] - prediction_int
        residuals[i - order] = residual
    
    return residuals


@njit
def _apply_ar_residuals_lossy_kernel_channel(data: np.ndarray, coeffs: np.ndarray, step: int) -> np.ndarray:
    """Numba-optimized kernel for computing AR residuals with lossy quantization (single channel)."""
    order = len(coeffs)
    n = len(data)
    residuals = np.empty(n - order, dtype=data.dtype)
    
    # Pre-allocate reconstructed array for efficiency
    reconstructed = np.empty(n, dtype=np.int16)
    reconstructed[:order] = data[:order]
    
    # Convert step to float32 for consistent float arithmetic
    step_f32 = np.float32(step)
    
    for i in range(order, n):
        # Predict using previous 'order' samples from reconstructed data
        # Use float32 accumulation
        prediction = np.float32(0.0)
        for j in range(order):
            prediction += coeffs[j] * np.float32(reconstructed[i - j - 1])
        
        # Round to nearest integer
        prediction_int = np.int16(np.round(prediction))
        
        # Compute residual from original data
        residual = data[i] - prediction_int
        
        # Quantize residual to nearest multiple of step
        quantized_residual = np.int16(np.round(np.float32(residual) / step_f32) * step_f32)
        residuals[i - order] = quantized_residual
        
        # Reconstruct sample using quantized residual for future predictions
        reconstructed[i] = prediction_int + quantized_residual
    
    return residuals


def apply_ar_residuals(data: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    """
    Apply AR model with given coefficients and return residuals.
    
    Args:
        data: Input data array (timepoints x channels)
        coeffs: AR coefficients (channels x order)
        
    Returns:
        Residuals array (timepoints x channels)
    """
    # Ensure coeffs is float32
    coeffs = np.array(coeffs, dtype=np.float32)
    
    n_timepoints, n_channels = data.shape
    order = coeffs.shape[1]
    residuals = np.zeros((n_timepoints - order, n_channels), dtype=data.dtype)
    
    for ch in range(n_channels):
        residuals[:, ch] = _apply_ar_residuals_kernel_channel(data[:, ch], coeffs[ch])
    
    return residuals


def apply_ar_residuals_lossy(data: np.ndarray, coeffs: np.ndarray, step: int) -> np.ndarray:
    """
    Apply AR model with given coefficients and return lossy residuals.
    
    Args:
        data: Input data array (timepoints x channels)
        coeffs: AR coefficients (channels x order)
        step: Quantization step size
        
    Returns:
        Residuals array (timepoints x channels)
    """
    coeffs = np.array(coeffs, dtype=np.float32)
    
    n_timepoints, n_channels = data.shape
    order = coeffs.shape[1]
    residuals = np.zeros((n_timepoints - order, n_channels), dtype=data.dtype)
    
    for ch in range(n_channels):
        residuals[:, ch] = _apply_ar_residuals_lossy_kernel_channel(data[:, ch], coeffs[ch], step)
    
    return residuals


def encode_ar(data: np.ndarray, order: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Encode data using AR model - returns coefficients, residuals, and initial values.
    
    Args:
        data: Input data array (timepoints x channels, int16)
        order: AR model order
        
    Returns:
        Tuple of (coefficients, residuals, initial_values)
        - coefficients: channels x order (float32)
        - residuals: (timepoints - order) x channels (int16)
        - initial_values: order x channels (int16)
    """
    # Fit AR model
    coeffs = fit_ar_model(data, order)
    
    # Convert coefficients to float32 to match what will be deserialized
    coeffs = coeffs.astype(np.float32)
    
    # Compute residuals using float32 coefficients
    residuals = apply_ar_residuals(data, coeffs)
    
    # Store initial values
    initial_values = data[:order, :]
    
    return coeffs, residuals, initial_values


def encode_ar_lossy(data: np.ndarray, order: int, step: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Encode data using AR model with lossy quantization.
    
    Args:
        data: Input data array (timepoints x channels, int16)
        order: AR model order
        step: Quantization step size
        
    Returns:
        Tuple of (coefficients, residuals, initial_values)
        - coefficients: channels x order (float32)
        - residuals: (timepoints - order) x channels (int16)
        - initial_values: order x channels (int16)
    """
    # Fit AR model
    coeffs = fit_ar_model(data, order)
    
    # Convert coefficients to float32 to match what will be deserialized
    coeffs = coeffs.astype(np.float32)
    
    # Compute residuals using float32 coefficients
    residuals = apply_ar_residuals_lossy(data, coeffs, step=step)
    
    # Store initial values
    initial_values = data[:order, :]
    
    return coeffs, residuals, initial_values


@njit
def _decode_ar_kernel_channel(coeffs: np.ndarray, residuals: np.ndarray, initial_values: np.ndarray) -> np.ndarray:
    """Numba-optimized kernel for AR decoding (single channel)."""
    order = len(coeffs)
    n = len(residuals) + order
    reconstructed = np.empty(n, dtype=np.int16)
    reconstructed[:order] = initial_values
    
    for i in range(order, n):
        # Predict using AR model
        # Use float32 accumulation
        prediction = np.float32(0.0)
        for j in range(order):
            prediction += coeffs[j] * np.float32(reconstructed[i - j - 1])
        
        # Round to nearest integer using numpy's round (banker's rounding)
        prediction_int = np.int16(np.round(prediction))
        
        # Add residual
        reconstructed[i] = prediction_int + residuals[i - order]
    
    return reconstructed


def decode_ar(coeffs: np.ndarray, residuals: np.ndarray, initial_values: np.ndarray) -> np.ndarray:
    """
    Decode AR encoded data.
    
    Args:
        coeffs: AR coefficients (channels x order, float32)
        residuals: Residuals array ((timepoints - order) x channels)
        initial_values: Initial values (order x channels)
        
    Returns:
        Reconstructed data array (timepoints x channels)
    """
    # Ensure coeffs is float32
    coeffs = np.array(coeffs, dtype=np.float32)
    
    n_channels = coeffs.shape[0]
    order = coeffs.shape[1]
    n_residuals = residuals.shape[0]
    n_timepoints = n_residuals + order
    
    reconstructed = np.zeros((n_timepoints, n_channels), dtype=np.int16)
    
    for ch in range(n_channels):
        reconstructed[:, ch] = _decode_ar_kernel_channel(coeffs[ch], residuals[:, ch], initial_values[:, ch])
    
    return reconstructed


# Warmup numba functions on module import
_warmup_numba_functions()
