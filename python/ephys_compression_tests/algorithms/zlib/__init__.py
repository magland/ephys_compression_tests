import numpy as np
import os
import zlib
from ...types import Algorithm

SOURCE_FILE = "zlib/__init__.py"


def _load_long_description():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(current_dir, "zlib.md")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


LONG_DESCRIPTION = _load_long_description()


def zlib_encode(x: np.ndarray, level: int = 9) -> bytes:
    """Encode numpy array using zlib compression.
    
    Args:
        x: Input numpy array
        level: Compression level (0-9, default 9 for maximum compression)
    
    Returns:
        Compressed bytes
    """
    # Store dtype and shape information
    dtype_str = str(x.dtype)
    shape_bytes = np.array(x.shape, dtype=np.int64).tobytes()
    dtype_bytes = dtype_str.encode('utf-8')
    dtype_len = np.array([len(dtype_bytes)], dtype=np.uint32).tobytes()
    
    # Compress the array data
    data_bytes = x.tobytes()
    compressed_data = zlib.compress(data_bytes, level=level)
    
    # Combine metadata and compressed data
    return dtype_len + dtype_bytes + shape_bytes + compressed_data


def zlib_decode(x: bytes, dtype: str, shape: tuple) -> np.ndarray:
    """Decode zlib compressed bytes back to numpy array.
    
    Args:
        x: Compressed bytes
        dtype: Expected numpy dtype
        shape: Expected array shape
    
    Returns:
        Decompressed numpy array
    """
    # Read dtype length
    dtype_len = np.frombuffer(x[:4], dtype=np.uint32)[0]
    offset = 4
    
    # Read dtype string (not used but stored for completeness)
    # dtype_str = x[offset:offset + dtype_len].decode('utf-8')
    offset += dtype_len
    
    # Read shape (not used but stored for completeness)
    # Determine number of dimensions from shape parameter
    num_dims = len(shape)
    shape_size = num_dims * 8  # int64
    # stored_shape = np.frombuffer(x[offset:offset + shape_size], dtype=np.int64)
    offset += shape_size
    
    # Decompress the data
    compressed_data = x[offset:]
    decompressed_data = zlib.decompress(compressed_data)
    
    # Reconstruct array
    arr = np.frombuffer(decompressed_data, dtype=np.dtype(dtype))
    return arr.reshape(shape)


algorithm_dicts_base = [
    {
        "name": "zlib",
        "version": "1",
        "encode": lambda x: zlib_encode(x, level=9),
        "decode": lambda x, dtype, shape: zlib_decode(x, dtype, shape),
        "description": "zlib compression at level 9 (maximum compression)",
        "tags": ["zlib"],
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

algorithms = [
    Algorithm(**a)
    for a in algorithm_dicts
]
