import os
import json
from typing import Optional, Dict, Any
import numpy as np
from ._memobin import (
    construct_memobin_url,
    download_from_memobin,
)


def check_cached_result(
    cache_dir: str,
    dataset_name: str,
    algorithm_name: str,
    algorithm_version: str,
    dataset_version: str,
    system_version: str,
    force: bool = False,
    verbose: bool = True,
) -> Optional[Dict[str, Any]]:
    """Check for cached benchmark results locally and in memobin.

    Args:
        cache_dir: Directory containing cached results
        dataset_name: Name of the dataset
        algorithm_name: Name of the algorithm
        algorithm_version: Version of the algorithm
        dataset_version: Version of the dataset
        system_version: Version of the system
        force: If True, ignore cached results
        verbose: Whether to print progress messages

    Returns:
        Cached result dictionary if found and valid, None otherwise
    """
    test_dir = os.path.join(cache_dir, dataset_name, algorithm_name)
    metadata_file = os.path.join(test_dir, "metadata.json")

    # First try local cache (unless force flag is set)
    cached_data = None
    if not force and os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            cached_data = json.load(f)
            # if versions do not match, then set to None
            if isinstance(cached_data, dict) and "result" in cached_data:
                result = cached_data["result"]
                if (
                    result["algorithm_version"] != algorithm_version
                    or result["dataset_version"] != dataset_version
                    or result.get("system_version", "") != system_version
                ):
                    cached_data = None

    # If not in local cache, try memobin (unless force flag is set)
    if cached_data is None and not force:
        memobin_url = construct_memobin_url(
            algorithm_name,
            dataset_name,
            algorithm_version,
            dataset_version,
            system_version,
            "metadata.json",
        )
        if verbose:
            print("  Looking for cached result in memobin...")
        cached_data = download_from_memobin(memobin_url)
        if cached_data is not None:
            if verbose:
                print("  Found result in memobin, saving locally...")
            # Save to local cache
            os.makedirs(test_dir, exist_ok=True)
            with open(metadata_file, "w") as f:
                json.dump(cached_data, f, indent=2)

    if (
        cached_data is not None
        and isinstance(cached_data, dict)
        and "result" in cached_data
    ):
        result = cached_data["result"]
        if (
            isinstance(result, dict)
            and result.get("algorithm_version") == algorithm_version
            and result.get("dataset_version") == dataset_version
            and result.get("system_version", "") == system_version
        ):
            result["cache_status"] = "cached"
            return result

    return None


def save_result_to_cache(
    result: Dict[str, Any],
    encoded_data: bytes,
    cache_dir: str,
    dataset_name: str,
    algorithm_name: str,
    reconstructed_data: Optional[np.ndarray] = None,
) -> None:
    """Save benchmark result and compressed data to cache.

    Args:
        result: Benchmark result dictionary
        encoded_data: Compressed data bytes
        cache_dir: Directory to store cached results
        dataset_name: Name of the dataset
        algorithm_name: Name of the algorithm
        reconstructed_data: Optional reconstructed array for lossy algorithms
    """
    test_dir = os.path.join(cache_dir, dataset_name, algorithm_name)
    metadata_file = os.path.join(test_dir, "metadata.json")
    compressed_file = os.path.join(test_dir, "compressed.dat")
    reconstructed_file = os.path.join(test_dir, "reconstructed.dat")

    os.makedirs(test_dir, exist_ok=True)
    cache_data = {"result": result}

    with open(metadata_file, "w") as f:
        json.dump(cache_data, f, indent=2)
    with open(compressed_file, "wb") as f:
        f.write(encoded_data)
    
    # Save reconstructed data for lossy algorithms
    if reconstructed_data is not None:
        with open(reconstructed_file, "wb") as f:
            f.write(reconstructed_data.tobytes())
