from typing import Callable
import numpy as np

class Algorithm:
    def __init__(self, *,
        name: str,
        version: str,
        encode: Callable[[np.ndarray], bytes],
        decode: Callable[[bytes, np.dtype, tuple], np.ndarray],
        description: str,
        tags: list[str],
        source_file: str,
        long_description: str
    ):
        self.name = name
        self.version = version
        self.encode = encode
        self.decode = decode
        self.description = description
        self.tags = tags
        self.source_file = source_file
        self.long_description = long_description

class Dataset:
    def __init__(self, *,
        name: str,
        version: str,
        create: Callable[[], np.ndarray],
        description: str,
        tags: list[str],
        source_file: str,
        long_description: str,
        ideal_compression_ratio: float = 0
    ):
        self.name = name
        self.version = version
        self.create = create
        self.description = description
        self.tags = tags
        self.source_file = source_file
        self.long_description = long_description
        self.ideal_compression_ratio = ideal_compression_ratio
