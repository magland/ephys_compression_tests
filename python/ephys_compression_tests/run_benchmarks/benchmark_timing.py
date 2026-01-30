from typing import Any, Tuple, Callable, Dict
from statistics import median
import time
import numpy as np


def run_timed_trials(
    data: np.ndarray, operation: Callable, *args
) -> Tuple[float, float, Any]:
    """Run multiple trials of an operation until total time exceeds 1 second.

    Args:
        data: Input numpy array for calculating throughput
        operation: Function to benchmark
        *args: Arguments to pass to the operation

    Returns:
        Tuple containing:
        - median_time: Median execution time across trials
        - mb_per_sec: Throughput in MB/s
        - result: Result from the last trial execution
    """
    times = []
    total_time = 0
    array_size_mb = data.nbytes / (1024 * 1024)  # Convert to MB

    operation(
        *args
    )  # execute once prior to timing in case there's any initial overhead

    ret = None
    while total_time < 1.0:
        start_time = time.perf_counter()
        ret = operation(*args)  # Execute operation
        trial_time = time.perf_counter() - start_time
        times.append(trial_time)
        total_time += trial_time

    median_time = median(times)
    mb_per_sec = array_size_mb / median_time
    return median_time, mb_per_sec, ret


def run_compression_benchmark(
    data: np.ndarray,
    algorithm_name: str,
    encode_fn: Callable,
    decode_fn: Callable,
    verbose: bool = True,
    lossy: bool = False,
) -> Tuple[Dict[str, Any], bytes, np.ndarray]:
    """Run compression and decompression benchmarks for an algorithm.

    Args:
        data: Input numpy array to compress
        algorithm_name: Name of the algorithm being benchmarked
        encode_fn: Compression function
        decode_fn: Decompression function
        verbose: Whether to print progress messages
        lossy: Whether the algorithm is lossy

    Returns:
        Tuple containing:
        - result: Dictionary with benchmark metrics
        - encoded: Compressed data bytes
        - decoded: Decompressed data array
    """
    if data.ndim == 1:
        data = data[:, np.newaxis]
    original_size = len(data.tobytes())
    dtype = str(data.dtype)

    if verbose:
        print("  Encoding...")
    encode_time, encode_mb_per_sec, encoded = run_timed_trials(data, encode_fn, data)
    compressed_size = len(encoded)
    compression_ratio = original_size / compressed_size

    if verbose:
        print("  Compression complete:")
        print(f"    Compressed size: {compressed_size:,} bytes")
        print(f"    Compression ratio: {compression_ratio:.2f}x")
        print(f"    Encode time: {encode_time*1000:.2f}ms")
        print(f"    Encode throughput: {encode_mb_per_sec:.2f} MB/s")
        print("  Decoding...")

    decode_time, decode_mb_per_sec, decoded = run_timed_trials(
        data, decode_fn, encoded, dtype, data.shape
    )

    if verbose:
        print(f"    Decode time: {decode_time*1000:.2f}ms")
        print(f"    Decode throughput: {decode_mb_per_sec:.2f} MB/s")

    # Verify correctness
    if len(data) != len(decoded):
        raise ValueError(
            f"Decompression failed: decoded length {len(decoded)} != original length {len(data)}"
        )

    if not lossy:
        if not np.array_equal(data, decoded):
            print(data[:100])
            print(decoded[:100])
            for j in range(len(data)):
                if data[j] != decoded[j]:
                    print(f"Error at index {j}: {data[j]} != {decoded[j]}")
                    break
            raise ValueError(f"Decompression verification failed for {algorithm_name}")
        rmse = 0.0
        max_error = 0.0
    else:
        # compute RMSE and max error
        rmse = float(np.sqrt(np.mean((data - decoded) ** 2)))
        max_error = float(np.max(np.abs(data - decoded)))
        print(f"    RMSE: {rmse:.4f}, Max error: {max_error:.4f}")

    if verbose:
        print("  Verification successful!")

    result = {
        "compression_ratio": compression_ratio,
        "encode_time": encode_time,
        "decode_time": decode_time,
        "encode_mb_per_sec": encode_mb_per_sec,
        "decode_mb_per_sec": decode_mb_per_sec,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "array_shape": data.shape,
        "array_dtype": dtype,
        "timestamp": time.time(),
        "cache_status": "new",
        "rmse": rmse,
        "max_error": max_error,
    }

    return result, encoded, decoded
