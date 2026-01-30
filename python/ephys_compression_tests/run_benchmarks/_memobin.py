import json
import requests
import time
from typing import Optional, TypeVar, Callable

T = TypeVar("T")


def _retry_with_backoff(
    func: Callable[..., T], num_retries: int = 4, *args, **kwargs
) -> T:
    """Execute a function with exponential backoff retry logic.

    Args:
        func: Function to execute
        num_retries: Maximum number of retries
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function

    Returns:
        The function's return value

    Raises:
        The last exception encountered after all retries are exhausted
    """
    last_exception = None
    for attempt in range(num_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed with error: {str(e)}")
            last_exception = e
            if attempt < num_retries - 1:
                sleep_time = 2**attempt  # 1, 2, 4, 8 seconds
                time.sleep(sleep_time)
            else:
                raise last_exception
    raise RuntimeError("Unexpected: retry loop completed without return or raise")


def create_signed_upload_url(
    url: str, size: int, user_id: str, memobin_api_key: str, num_retries: int = 4
) -> str:
    """Create a signed upload URL for memobin.

    Args:
        url: The target URL for the file
        size: Size of the file in bytes
        user_id: User ID for memobin
        memobin_api_key: API key for memobin authentication

    Returns:
        The signed upload URL

    Raises:
        ValueError: If the URL prefix is invalid
        requests.RequestException: If the API request fails
    """

    def _create_url() -> str:
        prefix = "https://tempory.net/f/memobin/"
        if not url.startswith(prefix):
            raise ValueError("Invalid url. Does not have proper prefix")

        file_path = url[len(prefix) :]
        tempory_api_url = "https://hub.tempory.net/api/uploadFile"

        response = requests.post(
            tempory_api_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {memobin_api_key}",
            },
            json={
                "appName": "memobin",
                "filePath": file_path,
                "size": size,
                "userId": user_id,
            },
        )

        if not response.ok:
            raise requests.RequestException("Failed to get signed url")

        result = response.json()
        upload_url = result["uploadUrl"]
        download_url = result["downloadUrl"]

        if download_url != url:
            raise ValueError(f"Mismatch between download url and url: {download_url} != {url}")

        return upload_url

    return _retry_with_backoff(_create_url, num_retries)


def construct_memobin_url(
    alg_name: str,
    dataset_name: str,
    alg_version: str,
    dataset_version: str,
    system_version: str,
    file_type: str = "metadata.json",
) -> str:
    """Construct the memobin URL for a specific benchmark result or dataset.

    Args:
        alg_name: Name of the algorithm
        dataset_name: Name of the dataset
        alg_version: Version of the algorithm
        dataset_version: Version of the dataset
        system_version: Version of the system
        file_type: Type of file (metadata.json or data.bin)

    Returns:
        The constructed memobin URL
    """
    path = f"{alg_name}/{dataset_name}/{alg_version}/{dataset_version}/{system_version}/{file_type}"
    return f"https://tempory.net/f/memobin/ephys_compression_tests/{path}"


def construct_dataset_url(
    dataset_name: str, dataset_version: str, format: str = "dat"
) -> str:
    """Construct the memobin URL for a dataset.

    Args:
        dataset_name: Name of the dataset
        dataset_version: Version of the dataset
        format: File format ("dat", "npy", or "json")

    Returns:
        The constructed memobin URL for the dataset
    """
    path = f"datasets/{dataset_name}/{dataset_version}/{dataset_name}-{dataset_version}.{format}"
    return f"https://tempory.net/f/memobin/ephys_compression_tests/{path}"


def upload_to_memobin(
    data: dict | bytes,
    url: str,
    memobin_api_key: str,
    content_type: str = "application/json",
    num_retries: int = 4,
) -> None:
    """Upload data to memobin.

    Args:
        data: The data to upload (dict for JSON or bytes for binary)
        url: The target URL for the file
        memobin_api_key: API key for memobin authentication
        content_type: Content type of the data

    Raises:
        requests.RequestException: If the upload fails
    """
    if isinstance(data, dict):
        data_bytes = json.dumps(data).encode("utf-8")
    else:
        data_bytes = data
    size = len(data_bytes)

    def _do_upload() -> None:
        upload_url = create_signed_upload_url(
            url, size, "ephys_compression_tests", memobin_api_key, num_retries
        )

        response = requests.put(
            upload_url, data=data_bytes, headers={"Content-Type": content_type}
        )

        if not response.ok:
            raise requests.RequestException("Failed to upload data to memobin")

    _retry_with_backoff(_do_upload, num_retries)


def exists_in_memobin(url: str, num_retries: int = 4) -> bool:
    """Check if a file exists in memobin using a HEAD request.

    Args:
        url: The URL to check

    Returns:
        True if the file exists, False otherwise
    """

    def _check_exists() -> bool:
        try:
            response = requests.head(url)
            return (
                200 <= response.status_code < 300
            )  # Any 2xx status code indicates success
        except requests.RequestException:
            return False

    return _retry_with_backoff(_check_exists, num_retries)


def download_from_memobin(
    url: str, as_json: bool = True, num_retries: int = 4
) -> Optional[dict | bytes]:
    """Download data from memobin.

    Args:
        url: The URL to download from
        as_json: Whether to parse the response as JSON

    Returns:
        The downloaded data as a dictionary or bytes, or None if not found

    Raises:
        requests.RequestException: If the download fails for a reason other than 404
    """

    def _do_download() -> Optional[dict | bytes]:
        response = None
        try:
            response = requests.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json() if as_json else response.content
        except requests.RequestException as e:
            if response and response.status_code == 404:
                return None
            raise e

    return _retry_with_backoff(_do_download, num_retries)
