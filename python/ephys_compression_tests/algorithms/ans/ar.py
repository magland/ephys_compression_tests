"""Auto-regressive model utilities for ANS compression."""

import numpy as np
from typing import Tuple
from numba import njit


def _warmup_numba_functions():
    """Warmup numba JIT compilation with small test data."""
    print("Warming up numba functions for AR model...")
    # Create small test data
    test_data = np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=np.int16)
    test_coeffs = np.array([0.5, 0.3], dtype=np.float32)
    test_residuals = np.array([1, 2, 3, 4], dtype=np.int16)
    test_initial = np.array([1, 2], dtype=np.int16)
    test_step = 2
    
    # Warmup each numba function
    _create_design_matrix(test_data, 2)
    _apply_ar_residuals_kernel(test_data, test_coeffs)
    _apply_ar_residuals_lossy_kernel(test_data, test_coeffs, test_step)
    _decode_ar_kernel(test_coeffs, test_residuals, test_initial)


@njit
def _create_design_matrix(data: np.ndarray, order: int) -> Tuple[np.ndarray, np.ndarray]:
    """Numba-optimized design matrix creation for AR model."""
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
        data: Input data array
        order: AR model order
        
    Returns:
        AR coefficients as numpy array
    """
    n = len(data)
    if order >= n:
        raise ValueError(f"AR order {order} must be less than data length {n}")
    
    # Create design matrix using numba-optimized function
    X_design, y_target = _create_design_matrix(data, order)
    
    # Use faster solve via normal equations: (X^T X) coeffs = X^T y
    # This is faster than lstsq for overdetermined systems
    XtX = X_design.T @ X_design
    Xty = X_design.T @ y_target
    coeffs = np.linalg.solve(XtX, Xty)
    
    return coeffs


@njit
def _apply_ar_residuals_kernel(data: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    """Numba-optimized kernel for computing AR residuals."""
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
def _apply_ar_residuals_lossy_kernel(data: np.ndarray, coeffs: np.ndarray, step: int) -> np.ndarray:
    """Numba-optimized kernel for computing AR residuals with lossy quantization."""
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
        data: Input data array
        coeffs: AR coefficients
        
    Returns:
        Residuals array
    """
    # Ensure coeffs is float32
    coeffs = np.array(coeffs, dtype=np.float32)
    
    return _apply_ar_residuals_kernel(data, coeffs)


def apply_ar_residuals_lossy(data: np.ndarray, coeffs: np.ndarray, step: int) -> np.ndarray:
    coeffs = np.array(coeffs, dtype=np.float32)
    return _apply_ar_residuals_lossy_kernel(data, coeffs, step)


def encode_ar(data: np.ndarray, order: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Encode data using AR model - returns coefficients, residuals, and initial values.
    
    Args:
        data: Input data array (int16)
        order: AR model order
        
    Returns:
        Tuple of (coefficients, residuals, initial_values)
    """
    # Fit AR model
    coeffs = fit_ar_model(data, order)
    
    # Convert coefficients to float32 to match what will be deserialized
    coeffs = coeffs.astype(np.float32)
    
    # Compute residuals using float32 coefficients
    residuals = apply_ar_residuals(data, coeffs)
    
    # Store initial values
    initial_values = data[:order]
    
    return coeffs, residuals, initial_values

def encode_ar_lossy(data: np.ndarray, order: int, step: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Fit AR model
    coeffs = fit_ar_model(data, order)
    
    # Convert coefficients to float32 to match what will be deserialized
    coeffs = coeffs.astype(np.float32)
    
    # Compute residuals using float32 coefficients
    residuals = apply_ar_residuals_lossy(data, coeffs, step=step)
    
    # Store initial values
    initial_values = data[:order]
    
    return coeffs, residuals, initial_values


@njit
def _decode_ar_kernel(coeffs: np.ndarray, residuals: np.ndarray, initial_values: np.ndarray) -> np.ndarray:
    """Numba-optimized kernel for AR decoding."""
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
        coeffs: AR coefficients (float32)
        residuals: Residuals array
        initial_values: Initial values (first 'order' samples)
        
    Returns:
        Reconstructed data array
    """
    # Ensure coeffs is float32
    coeffs = np.array(coeffs, dtype=np.float32)
    
    return _decode_ar_kernel(coeffs, residuals, initial_values)


# Warmup numba functions on module import
_warmup_numba_functions()

