import numpy as np
from ._memobin import (
    construct_reconstructed_url,
    exists_in_memobin,
    upload_to_memobin,
)


def upload_reconstructed_to_memobin(
    data: np.ndarray,
    algorithm_name: str,
    dataset_name: str,
    algorithm_version: str,
    dataset_version: str,
    system_version: str,
    memobin_api_key: str,
    verbose: bool = True,
) -> None:
    """Upload reconstructed array to memobin as raw .dat format.

    Args:
        data: The reconstructed numpy array to upload
        algorithm_name: Name of the algorithm
        dataset_name: Name of the dataset
        algorithm_version: Version of the algorithm
        dataset_version: Version of the dataset
        system_version: Version of the system
        memobin_api_key: API key for memobin
        verbose: Whether to print progress messages
    """
    try:
        # Upload raw .dat format
        reconstructed_url_raw = construct_reconstructed_url(
            algorithm_name, dataset_name, algorithm_version, dataset_version, system_version, "dat"
        )
        if not exists_in_memobin(reconstructed_url_raw):
            if verbose:
                print("  Uploading reconstructed array to memobin...")
            upload_to_memobin(
                data.tobytes(),
                reconstructed_url_raw,
                memobin_api_key,
                content_type="application/octet-stream",
            )
            if verbose:
                print("  Successfully uploaded reconstructed data")
    except Exception as e:
        print(f"  Warning: Failed to upload reconstructed data to memobin: {str(e)}")
