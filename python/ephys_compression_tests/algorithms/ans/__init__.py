import numpy as np
import os
from .ar import encode_ar, decode_ar
from ...types import Algorithm

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
    symbol_values: np.ndarray
) -> bytes:
    section1 = np.array([dtype_code, num_words, signal_length, len(symbol_counts)], dtype=np.uint32)
    section2 = np.array([state], dtype=np.uint64)
    symbol_counts_bytes = symbol_counts.astype(np.uint32).tobytes()
    symbol_values_bytes = symbol_values.tobytes()

    return section1.tobytes() + section2.tobytes() + symbol_counts_bytes + symbol_values_bytes

def unpack_ans_header(header_bytes: bytes) -> dict:
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
    }


def ans_encode_0(x: np.ndarray) -> bytes:
    from simple_ans import ans_encode

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
        x_diff = np.diff(x)
        x0 = x[0:1]
        encoded_diff = a["encode"](x_diff)
        # Store the first value at the start
        first_value_bytes = x0.tobytes()
        return first_value_bytes + encoded_diff
    def decode0(x: bytes, dtype: str, shape: tuple, a=a) -> np.ndarray:
        dtype_np = np.dtype(dtype)
        num_bytes_first_value = dtype_np.itemsize
        first_value_bytes = x[:num_bytes_first_value]
        x0 = np.frombuffer(first_value_bytes, dtype=dtype_np)
        encoded_diff = x[num_bytes_first_value:]
        x_diff = a["decode"](encoded_diff, dtype, (shape[0]-1,))
        x_reconstructed = np.empty(shape, dtype=dtype_np)
        x_reconstructed[0] = x0
        x_reconstructed[1:] = x0 + np.cumsum(x_diff)
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
    def encode0(x: np.ndarray, a=a) -> bytes:
        x_diff = np.diff(np.diff(x))
        x0 = x[0:1]
        encoded_diff = a["encode"](x_diff)
        # Store the first value at the start
        first_value_bytes = x0.tobytes()
        second_value_bytes = x[1:2].tobytes()
        return first_value_bytes + second_value_bytes + encoded_diff
    def decode0(x: bytes, dtype: str, shape: tuple, a=a) -> np.ndarray:
        dtype_np = np.dtype(dtype)
        num_bytes_first_value = dtype_np.itemsize
        first_value_bytes = x[:num_bytes_first_value]
        second_value_bytes = x[num_bytes_first_value:2*num_bytes_first_value]
        x0 = np.frombuffer(first_value_bytes, dtype=dtype_np)
        x1 = np.frombuffer(second_value_bytes, dtype=dtype_np)
        encoded_diff2 = x[2*num_bytes_first_value:]
        x_diff2 = a["decode"](encoded_diff2, dtype, (shape[0]-2,))
        x_recon1 = np.empty((shape[0]-1,), dtype=dtype_np)
        x_recon1[0] = x1 - x0
        x_recon1[1:] = x_recon1[0] + np.cumsum(x_diff2)
        x_reconstructed = np.empty(shape, dtype=dtype_np)
        x_reconstructed[0] = x0
        x_reconstructed[1:] = x0 + np.cumsum(x_recon1)
        return x_reconstructed
    algorithm_dicts.append({
        "name": a["name"] + "-delta2",
        "version": a["version"],
        "encode": encode0,
        "decode": decode0,
        "description": a["description"] + " with delta2 encoding",
        "tags": a["tags"] + ["delta2"],
        "source_file": a["source_file"],
        "long_description": a["long_description"]
    })

# Add auto-regressive prediction encoding
for a in algorithm_dicts_base:
    for order in [2, 8]:
        def encode0(x: np.ndarray, a=a, order=order) -> bytes:
            coeffs, residuals, initial_values = encode_ar(x, order=order)
            encoded_residuals = a["encode"](residuals)
            coeffs_bytes = coeffs.astype(np.float32).tobytes()
            initial_values_bytes = initial_values.astype(np.int16).tobytes()
            return coeffs_bytes + initial_values_bytes + encoded_residuals
        def decode0(x: bytes, dtype: str, shape: tuple, a=a, order=order) -> np.ndarray:
            dtype_np = np.dtype(dtype)
            num_bytes_coeffs = order * np.dtype(np.float32).itemsize
            coeffs_bytes = x[:num_bytes_coeffs]
            coeffs = np.frombuffer(coeffs_bytes, dtype=np.float32)
            num_initial_values = len(coeffs)
            num_bytes_initial_values = num_initial_values * dtype_np.itemsize
            initial_values_bytes = x[num_bytes_coeffs : num_bytes_coeffs + num_bytes_initial_values]
            initial_values = np.frombuffer(initial_values_bytes, dtype=dtype_np)
            encoded_residuals = x[num_bytes_coeffs + num_bytes_initial_values :]
            residuals = a["decode"](encoded_residuals, dtype, (shape[0]-num_initial_values,))
            reconstructed = decode_ar(coeffs, residuals, initial_values)
            return reconstructed.reshape(shape)
        algorithm_dicts.append({
            "name": a["name"] + f"-ar{order}",
            "version": a["version"],
            "encode": encode0,
            "decode": decode0,
            "description": a["description"] + f" with auto-regressive prediction encoding of order {order}",
            "tags": a["tags"] + [f"ar{order}"],
            "source_file": a["source_file"],
            "long_description": a["long_description"]
        })

algorithms = [
    Algorithm(**a)
    for a in algorithm_dicts
]