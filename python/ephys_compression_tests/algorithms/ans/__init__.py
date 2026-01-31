import numpy as np
import os
from . import lpc_numba
from ...types import Algorithm


# Adapter functions
def encode_lpc(data: np.ndarray, order: int):
    """Encode using LPC model - adapter for lpc_numba."""
    coeffs, initial_points = lpc_numba.fit_lpc_model(data, k=order)
    residuals_full = lpc_numba.compute_residuals(data, coeffs, initial_points)
    # Extract residuals excluding the initial points (first 'order' rows)
    residuals = residuals_full[order:, :]
    # Transpose initial_points to match old API: (order, channels)
    initial_values = initial_points.T
    return coeffs, residuals, initial_values


def encode_lpc_lossy(data: np.ndarray, order: int, step: int):
    """Encode using LPC model with lossy quantization - adapter for lpc_numba."""
    # Fit the LPC model
    coeffs, initial_points = lpc_numba.fit_lpc_model(data, k=order)

    # Compute residuals with quantization
    residuals_full = lpc_numba.compute_residuals_lossy(data, coeffs, initial_points, step=step)
    
    # Extract residuals excluding the initial points (first 'order' rows)
    residuals = residuals_full[order:, :]
    
    # Transpose initial_points to match old API: (order, channels)
    initial_values = initial_points.T
    return coeffs, residuals, initial_values


def decode_lpc(coeffs: np.ndarray, residuals: np.ndarray, initial_values: np.ndarray):
    """Decode LPC encoded data - adapter for lpc_numba."""
    # Transpose initial_values from (order, channels) to (channels, order)
    initial_points = initial_values.T
    
    # Create full residuals array including initial points
    order = coeffs.shape[1]
    n_residuals, n_channels = residuals.shape
    n_timepoints = n_residuals + order
    
    residuals_full = np.zeros((n_timepoints, n_channels), dtype=np.int16)
    residuals_full[:order, :] = initial_points.T
    residuals_full[order:, :] = residuals
    
    return lpc_numba.reconstruct_from_residuals(residuals_full, coeffs, initial_points)

SOURCE_FILE = "ans/__init__.py"


def _load_long_description():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(current_dir, "ans.md")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


LONG_DESCRIPTION = _load_long_description()

def create_ans_header(
    dtype_code: int,
    num_words: int,
    signal_length: int,
    state: np.uint64,
    symbol_counts: np.ndarray,
    symbol_values: np.ndarray,
    shape: tuple
) -> bytes:
    ndim = len(shape)
    section0 = np.array([ndim] + list(shape), dtype=np.uint32)
    section1 = np.array([dtype_code, num_words, signal_length, len(symbol_counts)], dtype=np.uint32)
    section2 = np.array([state], dtype=np.uint64)
    symbol_counts_bytes = symbol_counts.astype(np.uint32).tobytes()
    symbol_values_bytes = symbol_values.tobytes()

    return section0.tobytes() + section1.tobytes() + section2.tobytes() + symbol_counts_bytes + symbol_values_bytes

def unpack_ans_header(header_bytes: bytes) -> dict:
    # read section 0
    ndim = np.frombuffer(header_bytes[:4], dtype=np.uint32)[0]
    shape = tuple(np.frombuffer(header_bytes[4 : 4 + ndim * 4], dtype=np.uint32))
    offset = 4 + ndim * 4
    header_bytes = header_bytes[offset:]
    # read section 1
    section1_size = 4 * 4  # 4 uint32
    section1 = np.frombuffer(header_bytes[:section1_size], dtype=np.uint32)
    dtype_code = int(section1[0])
    num_words = int(section1[1])
    signal_length = int(section1[2])
    num_symbols = int(section1[3])
    # read section 2
    section2_size = 8  # 1 uint64
    section2 = np.frombuffer(header_bytes[section1_size : section1_size + section2_size], dtype=np.uint64)
    state = np.uint64(section2[0])
    # read symbol counts and values
    remaining_bytes = header_bytes[section1_size + section2_size :]
    symbol_counts = np.frombuffer(remaining_bytes[: num_symbols * 4], dtype=np.uint32)
    
    symbol_values_dtype = {0: np.uint8, 1: np.uint16, 2: np.uint32, 3: np.int16, 4: np.int32}.get(dtype_code)
    num_bytes_per_value = np.dtype(symbol_values_dtype).itemsize
    if symbol_values_dtype is None:
        raise ValueError(f"Unsupported dtype code: {dtype_code}")
    symbol_values = np.frombuffer(remaining_bytes[num_symbols * 4 : num_symbols * 4 + num_symbols * num_bytes_per_value], dtype=symbol_values_dtype)

    if len(symbol_counts) != len(symbol_values):
        raise ValueError("Mismatch between number of symbol counts and symbol values")

    return {
        "dtype_code": dtype_code,
        "num_words": num_words,
        "signal_length": signal_length,
        "state": state,
        "symbol_counts": symbol_counts,
        "symbol_values": symbol_values,
        "shape": shape
    }


def ans_encode_0(x: np.ndarray) -> bytes:
    from simple_ans import ans_encode

    shape0 = x.shape
    if x.ndim == 2:
        # flatten
        x = x.reshape(-1)

    encoded = ans_encode(x)
    if x.dtype == np.uint8:
        dtype_code = 0
    elif x.dtype == np.uint16:
        dtype_code = 1
    elif x.dtype == np.uint32:
        dtype_code = 2
    elif x.dtype == np.int16:
        dtype_code = 3
    elif x.dtype == np.int32:
        dtype_code = 4
    else:
        raise ValueError(f"Unsupported dtype: {x.dtype}")
    
    # Use the new header utilities
    header_bytes = create_ans_header(
        dtype_code=dtype_code,
        num_words=len(encoded.words),
        signal_length=encoded.signal_length,
        state=encoded.state,
        symbol_counts=encoded.symbol_counts,
        symbol_values=encoded.symbol_values,
        shape=shape0
    )

    header_size = np.array([len(header_bytes)], dtype="uint32")

    return header_size.tobytes() + header_bytes + encoded.words.tobytes()



def ans_decode_0(x: bytes, dtype: str, shape: tuple) -> np.ndarray:
    from simple_ans import ans_decode, EncodedSignal

    header_size = np.frombuffer(x[:4], dtype=np.uint32)[0]

    # Use the new header utilities
    header_dict = unpack_ans_header(x[4 : 4 + header_size])

    dtype_code = header_dict["dtype_code"]
    num_words = header_dict["num_words"]
    signal_length = header_dict["signal_length"]
    state = header_dict["state"]
    symbol_counts = header_dict["symbol_counts"]
    symbol_values = header_dict["symbol_values"]
    shape_from_header = header_dict["shape"]
    if shape != shape_from_header:
        raise ValueError("Shape mismatch between provided shape and shape in header")

    words_bytes = x[4 + header_size :]

    if dtype_code == 0:
        assert dtype == "uint8"
    elif dtype_code == 1:
        assert dtype == "uint16"
    elif dtype_code == 2:
        assert dtype == "uint32"
    elif dtype_code == 3:
        assert dtype == "int16"
    elif dtype_code == 4:
        assert dtype == "int32"
    else:
        raise ValueError(f"Unsupported dtype code: {dtype_code}")

    encoded = EncodedSignal(
        signal_length=int(signal_length),
        state=np.uint64(state),
        symbol_counts=symbol_counts.astype(np.uint32),
        symbol_values=symbol_values.astype(dtype),
        words=np.frombuffer(words_bytes, dtype=np.uint32, count=num_words),
    )
    return ans_decode(encoded).reshape(shape)

algorithm_dicts_base = [
    {
        "name": "ans",
        "version": "1",
        "encode": lambda x: ans_encode_0(x),
        "decode": lambda x, dtype, shape: ans_decode_0(x, dtype, shape),
        "description": "ANS",
        "tags": ["ans"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    }
]

algorithm_dicts = []
for a in algorithm_dicts_base:
    algorithm_dicts.append(a)

# add delta encoding
for a in algorithm_dicts_base:
    def encode0(x: np.ndarray, a=a) -> bytes:
        assert x.ndim == 2 and x.shape[0] > 1, "Input array must be 2D with more than one timepoint"
        x_diff = np.diff(x, axis=0)
        first_timepoint = x[0:1, :].flatten()
        encoded_diff = a["encode"](x_diff)
        # Store the first value at the start
        first_timepoint_bytes = first_timepoint.tobytes()
        return first_timepoint_bytes + encoded_diff
    def decode0(x: bytes, dtype: str, shape: tuple, a=a) -> np.ndarray:
        dtype_np = np.dtype(dtype)
        num_bytes_first_timepoint = dtype_np.itemsize * shape[1]
        first_timepoint_bytes = x[:num_bytes_first_timepoint]
        first_timepoint = np.frombuffer(first_timepoint_bytes, dtype=dtype_np)
        encoded_diff = x[num_bytes_first_timepoint:]
        x_diff = a["decode"](encoded_diff, dtype, (shape[0]-1, shape[1]))
        x_reconstructed = np.empty(shape, dtype=dtype_np)
        x_reconstructed[0] = first_timepoint
        x_reconstructed[1:] = first_timepoint + np.cumsum(x_diff, axis=0)
        return x_reconstructed
    algorithm_dicts.append({
        "name": a["name"] + "-delta",
        "version": a["version"],
        "encode": encode0,
        "decode": decode0,
        "description": a["description"] + " with delta encoding",
        "tags": a["tags"] + ["delta"],
        "source_file": a["source_file"],
        "long_description": a["long_description"]
    })

# add delta2 encoding
for a in algorithm_dicts_base:
    def encode0_lpc_lossy(x: np.ndarray, a=a) -> bytes:
        assert x.ndim == 2 and x.shape[0] > 2, "Input array must be 2D with more than two timepoints"
        x_diff = np.diff(np.diff(x, axis=0), axis=0)
        first_timepoint = x[0:1, :].flatten()
        second_timepoint = x[1:2, :].flatten()
        encoded_diff = a["encode"](x_diff)
        # Store the first value at the start
        first_timepoint_bytes = first_timepoint.tobytes()
        second_timepoint_bytes = second_timepoint.tobytes()
        return first_timepoint_bytes + second_timepoint_bytes + encoded_diff
    def decode0_lpc_lossy(x: bytes, dtype: str, shape: tuple, a=a) -> np.ndarray:
        dtype_np = np.dtype(dtype)
        num_bytes_first_timepoint = dtype_np.itemsize * shape[1]
        first_timepoint_bytes = x[:num_bytes_first_timepoint]
        second_timepoint_bytes = x[num_bytes_first_timepoint:2*num_bytes_first_timepoint]
        x0 = np.frombuffer(first_timepoint_bytes, dtype=dtype_np)
        x1 = np.frombuffer(second_timepoint_bytes, dtype=dtype_np)
        encoded_diff2 = x[2*num_bytes_first_timepoint:]
        x_diff2 = a["decode"](encoded_diff2, dtype, (shape[0]-2, shape[1]))
        x_recon1 = np.empty((shape[0]-1,shape[1]), dtype=dtype_np)
        x_recon1[0] = x1 - x0
        x_recon1[1:] = x_recon1[0] + np.cumsum(x_diff2, axis=0)
        x_reconstructed = np.empty(shape, dtype=dtype_np)
        x_reconstructed[0] = x0
        x_reconstructed[1:] = x0 + np.cumsum(x_recon1, axis=0)
        return x_reconstructed
    algorithm_dicts.append({
        "name": a["name"] + "-delta2",
        "version": a["version"],
        "encode": encode0_lpc_lossy,
        "decode": decode0_lpc_lossy,
        "description": a["description"] + " with delta2 encoding",
        "tags": a["tags"] + ["delta2"],
        "source_file": a["source_file"],
        "long_description": a["long_description"]
    })

# Add auto-regressive prediction encoding
for a in algorithm_dicts_base:
    for order in [2, 8]:
        def encode0_lpc(x: np.ndarray, a=a, order=order) -> bytes:
            assert x.ndim == 2 and x.shape[0] > order, f"Input array must be 2D (timepoints x channels) with more than {order} timepoints"
            coeffs, residuals, initial_values = encode_lpc(x, order=order)
            # coeffs: (n_channels x order), residuals: (n_timepoints-order x n_channels), initial_values: (order x n_channels)
            encoded_residuals = a["encode"](residuals)
            coeffs_bytes = coeffs.astype(np.float32).tobytes()
            initial_values_bytes = initial_values.astype(np.int16).tobytes()
            return coeffs_bytes + initial_values_bytes + encoded_residuals
        def decode0_lpc(x: bytes, dtype: str, shape: tuple, a=a, order=order) -> np.ndarray:
            assert len(shape) == 2, f"Shape must be 2D (timepoints x channels)"
            dtype_np = np.dtype(dtype)
            n_channels = shape[1]
            # coeffs is (n_channels x order)
            num_bytes_coeffs = n_channels * order * np.dtype(np.float32).itemsize
            coeffs_bytes = x[:num_bytes_coeffs]
            coeffs = np.frombuffer(coeffs_bytes, dtype=np.float32).reshape((n_channels, order))
            # initial_values is (order x n_channels)
            num_bytes_initial_values = order * n_channels * dtype_np.itemsize
            initial_values_bytes = x[num_bytes_coeffs : num_bytes_coeffs + num_bytes_initial_values]
            initial_values = np.frombuffer(initial_values_bytes, dtype=dtype_np).reshape((order, n_channels))
            encoded_residuals = x[num_bytes_coeffs + num_bytes_initial_values :]
            # residuals is ((shape[0]-order) x n_channels)
            residuals = a["decode"](encoded_residuals, dtype, (shape[0]-order, n_channels))
            reconstructed = decode_lpc(coeffs, residuals, initial_values)
            return reconstructed
        algorithm_dicts.append({
            "name": a["name"] + f"-lpc{order}",
            "version": a["version"] + f".3",
            "encode": encode0_lpc,
            "decode": decode0_lpc,
            "description": a["description"] + f" with auto-regressive prediction encoding of order {order}",
            "tags": a["tags"] + [f"lpc{order}"],
            "source_file": a["source_file"],
            "long_description": a["long_description"]
        })

# Add lossy lpc
for lpc_order in [2, 8]:
    for tolerance in [1, 2, 3, 4, 6, 8, 12, 16]:
        def make_encode_lpc_lossy(tolerance=tolerance, order=lpc_order):
            def encode0_lpc_lossy(x: np.ndarray) -> bytes:
                assert x.ndim == 2, f"Input array must be 2D (timepoints x channels)"
                coeffs, residuals, initial_values = encode_lpc_lossy(x, order=order, step=tolerance * 2 + 1)
                # coeffs: (n_channels x order), residuals: (n_timepoints-order x n_channels), initial_values: (order x n_channels)
                encoded_residuals = ans_encode_0(residuals)
                coeffs_bytes = coeffs.astype(np.float32).tobytes()
                initial_values_bytes = initial_values.astype(np.int16).tobytes()
                return coeffs_bytes + initial_values_bytes + encoded_residuals
            return encode0_lpc_lossy
        def make_decode_lpc_lossy(order=lpc_order):
            def decode0_lpc_lossy(x: bytes, dtype: str, shape: tuple) -> np.ndarray:
                assert len(shape) == 2, f"Shape must be 2D (timepoints x channels)"
                dtype_np = np.dtype(dtype)
                n_channels = shape[1]
                # coeffs is (n_channels x order)
                num_bytes_coeffs = n_channels * order * np.dtype(np.float32).itemsize
                coeffs_bytes = x[:num_bytes_coeffs]
                coeffs = np.frombuffer(coeffs_bytes, dtype=np.float32).reshape((n_channels, order))
                # initial_values is (order x n_channels)
                num_bytes_initial_values = order * n_channels * dtype_np.itemsize
                initial_values_bytes = x[num_bytes_coeffs : num_bytes_coeffs + num_bytes_initial_values]
                initial_values = np.frombuffer(initial_values_bytes, dtype=dtype_np).reshape((order, n_channels))
                encoded_residuals = x[num_bytes_coeffs + num_bytes_initial_values :]
                # residuals is ((shape[0]-order) x n_channels)
                residuals = ans_decode_0(encoded_residuals, dtype, (shape[0]-order, n_channels))
                reconstructed = decode_lpc(coeffs, residuals, initial_values)
                return reconstructed
            return decode0_lpc_lossy
        algorithm_dicts.append({
            "name": f"ans-lpc{lpc_order}-lossy-tol{tolerance}",
            "version": "12",
            "encode": make_encode_lpc_lossy(),
            "decode": make_decode_lpc_lossy(),
            "description": f"ANS with lossy linear predictive coding of order {lpc_order} and tolerance {tolerance}",
            "tags": ["ans", "lossy", f"lpc{lpc_order}"],
            "source_file": SOURCE_FILE,
            "long_description": LONG_DESCRIPTION
        })

algorithms = [
    Algorithm(**a)
    for a in algorithm_dicts
]