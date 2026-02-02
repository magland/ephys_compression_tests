from typing import Any, Dict, List
import time
from datetime import datetime
from ._memobin import (
    upload_to_memobin,
)


def upload_benchmark_status(
    memobin_api_key: str,
    current_dataset: str,
    current_algorithm: str,
    completed_benchmarks: List[Dict[str, Any]],
    total_benchmarks: int,
    start_time: float,
) -> None:
    """Upload current benchmark status to memobin.

    Args:
        memobin_api_key: API key for memobin authentication
        current_dataset: Name of the current dataset being processed
        current_algorithm: Name of the current algorithm being tested
        completed_benchmarks: List of completed benchmark results
        total_benchmarks: Total number of benchmarks to run
        start_time: Timestamp when the benchmark run started
    """
    status = {
        "current_dataset": current_dataset,
        "current_algorithm": current_algorithm,
        "completed_count": len(completed_benchmarks),
        "total_count": total_benchmarks,
        "progress_percentage": (len(completed_benchmarks) / total_benchmarks) * 100,
        "elapsed_time": time.time() - start_time,
        "last_update": datetime.now().isoformat(),
        "completed_benchmarks": completed_benchmarks,
    }

    status_url = "https://tempory.net/f/memobin/ephys_compression_tests/benchmark_status/current.json"
    upload_to_memobin(status, status_url, memobin_api_key)
