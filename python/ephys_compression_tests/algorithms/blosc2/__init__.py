import numpy as np
import os
import blosc2
from ...types import Algorithm

SOURCE_FILE = "blosc2/__init__.py"


def _load_long_description():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(current_dir, "blosc2.md")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


LONG_DESCRIPTION = _load_long_description()


def blosc2_encode(x: np.ndarray, clevel: int, codec, filter: int = 2) -> bytes:
    import blosc2

    # Convert filter int to proper enum
    if filter == 2:
        blosc_filter = blosc2.Filter.BITSHUFFLE
    elif filter == 1:
        blosc_filter = blosc2.Filter.SHUFFLE
    else:
        blosc_filter = blosc2.Filter.NOFILTER

    # Get typesize from numpy array
    typesize = x.dtype.itemsize

    # Compress data
    compressed = blosc2.compress(
        x,  # numpy arrays support buffer interface
        typesize=typesize,
        clevel=clevel,
        filter=blosc_filter,
        codec=codec,
    )
    assert isinstance(compressed, bytes)  # Type assertion
    return compressed


def blosc2_decode(x: bytes, dtype: str, shape: tuple) -> np.ndarray:
    import blosc2

    decompressed = blosc2.decompress(x)
    assert isinstance(decompressed, (bytes, bytearray))  # Type assertion
    arr = np.frombuffer(decompressed, dtype=np.dtype(dtype))
    return arr.reshape(shape)

zstd_codec = blosc2.Codec.ZSTD

algorithms_dicts = [
    {
        "name": "blosc2-zstd-1",
        "version": "1b",
        "encode": lambda x: blosc2_encode(x, clevel=1, codec=zstd_codec),
        "decode": lambda x, dtype, shape: blosc2_decode(x, dtype, shape),
        "description": "Blosc2 compression at level 1 (fastest compression).",
        "tags": ["blosc2"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "blosc2-zstd-5",
        "version": "1",
        "encode": lambda x: blosc2_encode(x, clevel=5, codec=zstd_codec),
        "decode": lambda x, dtype, shape: blosc2_decode(x, dtype, shape),
        "description": "Blosc2 compression at level 5 (balanced speed/compression).",
        "tags": ["blosc2"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "blosc2-zstd-9",
        "version": "1",
        "encode": lambda x: blosc2_encode(x, clevel=9, codec=zstd_codec),
        "decode": lambda x, dtype, shape: blosc2_decode(x, dtype, shape),
        "description": "Blosc2 compression at level 9 (maximum compression).",
        "tags": ["blosc2"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    }
]

algorithms = [
    Algorithm(**a)
    for a in algorithms_dicts
]