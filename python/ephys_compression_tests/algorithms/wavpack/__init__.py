import numpy as np
import os
from ...types import Algorithm

SOURCE_FILE = "wavpack/__init__.py"


def _load_long_description():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(current_dir, "wavpack.md")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


LONG_DESCRIPTION = _load_long_description()


def wavpack_encode(x: np.ndarray, bps: float=None) -> bytes:
    from wavpack_numcodecs import WavPack
    if bps is not None:
        codec = WavPack(bps=bps)
    else:
        codec = WavPack()
    encoded = codec.encode(x)
    assert isinstance(encoded, bytes)
    return encoded

def wavpack_decode(x: bytes, dtype: str, shape: tuple) -> np.ndarray:
    from wavpack_numcodecs import WavPack
    codec = WavPack()
    decoded = codec.decode(x)
    arr = np.frombuffer(decoded, dtype=np.dtype(dtype))
    return arr.reshape(shape)

algorithm_dicts_base = [
    {
        "name": "wavpack",
        "version": "1",
        "encode": lambda x: wavpack_encode(x),
        "decode": lambda x, dtype, shape: wavpack_decode(x, dtype, shape),
        "description": "WavPack",
        "tags": ["wavpack"],
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

# Add lossy versions
for bps in [3, 4, 5, 6]:
    algorithm_dicts.append({
        "name": f"wavpack-lossy-{bps}",
        "version": "1",
        "encode": lambda x: wavpack_encode(x, bps=bps),
        "decode": lambda x, dtype, shape: wavpack_decode(x, dtype, shape),
        "description": f"WavPack lossy with {bps} bits per sample",
        "tags": ["wavpack", "lossy"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    })

algorithms = [
    Algorithm(**a)
    for a in algorithm_dicts
]