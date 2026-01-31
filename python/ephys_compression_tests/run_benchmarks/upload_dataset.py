import os
import numpy as np
from ._memobin import (
    construct_dataset_url,
    exists_in_memobin,
    upload_to_memobin,
)


def upload_dataset_to_memobin(
    data: np.ndarray,
    dataset_name: str,
    dataset_version: str,
    memobin_api_key: str,
    cache_dir: str,
    verbose: bool = True,
) -> None:
    """Upload dataset to memobin in multiple formats.

    Args:
        data: The numpy array dataset to upload
        dataset_name: Name of the dataset
        dataset_version: Version of the dataset
        memobin_api_key: API key for memobin
        cache_dir: Directory for temporary files
        verbose: Whether to print progress messages
    """
    try:
        # Upload array metadata as JSON
        dataset_url_json = construct_dataset_url(dataset_name, dataset_version, "json")
        if not exists_in_memobin(dataset_url_json):
            if verbose:
                print("  Uploading dataset metadata to memobin...")
            metadata = {"dtype": str(data.dtype), "shape": data.shape}
            upload_to_memobin(
                metadata,
                dataset_url_json,
                memobin_api_key,
                content_type="application/json",
            )
            if verbose:
                print("  Successfully uploaded metadata")

        # Upload raw .dat format
        dataset_url_raw = construct_dataset_url(dataset_name, dataset_version, "dat")
        if not exists_in_memobin(dataset_url_raw):
            if verbose:
                print("  Uploading dataset (raw) to memobin...")
            upload_to_memobin(
                data.tobytes(),
                dataset_url_raw,
                memobin_api_key,
                content_type="application/octet-stream",
            )
            if verbose:
                print("  Successfully uploaded raw dataset")

        # Upload .npy format
        dataset_url_npy = construct_dataset_url(dataset_name, dataset_version, "npy")
        if not exists_in_memobin(dataset_url_npy):
            if verbose:
                print("  Uploading dataset (npy) to memobin...")
            # Save array to a temporary .npy file
            temp_npy = os.path.join(cache_dir, "temp.npy")
            np.save(temp_npy, data)
            with open(temp_npy, "rb") as f:
                npy_bytes = f.read()
            os.remove(temp_npy)  # Clean up temp file

            upload_to_memobin(
                npy_bytes,
                dataset_url_npy,
                memobin_api_key,
                content_type="application/octet-stream",
            )
            if verbose:
                print("  Successfully uploaded npy dataset")
    except Exception as e:
        print(f"  Warning: Failed to upload dataset to memobin: {str(e)}")
