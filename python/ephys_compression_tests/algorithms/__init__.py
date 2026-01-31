from .blosc2 import algorithms as blosc2_algorithms
from .ans import algorithms as ans_algorithms
from .wavpack import algorithms as wavpack_algorithms
from .lzma import algorithms as lzma_algorithms
from .zlib import algorithms as zlib_algorithms
from ..types import Algorithm

algorithms: list[Algorithm] = (
    blosc2_algorithms
    + ans_algorithms
    + wavpack_algorithms
    + lzma_algorithms
    + zlib_algorithms
)
