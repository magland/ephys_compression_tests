import os
import time
from typing import Dict, Any, List, Optional
import numpy as np

from ..algorithms import algorithms
from ..datasets import datasets
from ._memobin import construct_memobin_url, upload_to_memobin
from .upload_dataset import upload_dataset_to_memobin
from .cache_management import check_cached_result, save_result_to_cache
from .benchmark_timing import run_compression_benchmark
from .collect_info import collect_algorithm_info, collect_dataset_info
from .is_compatible import is_compatible
from .upload_benchmark_status import upload_benchmark_status
from ..types import Algorithm, Dataset

system_version = "v6"


def run_benchmarks(
    cache_dir: str = ".benchmark_cache",
    verbose: bool = True,
    selected_algorithms: Optional[List[Algorithm]] = None,
    selected_datasets: Optional[List[Dataset]] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """Run all benchmarks, with caching based on algorithm and dataset versions.

    Results are stored in separate directories for each dataset/algorithm combination:
    cache_dir/
        dataset_name/
            algorithm_name/
                metadata.json  # Contains algorithm version, dataset version, and results
                compressed.dat # The actual compressed data

    Args:
        cache_dir: Directory to store cached results
        verbose: Whether to print progress messages
        selected_algorithms: Optional list of specific algorithms to run
        selected_datasets: Optional list of specific datasets to run
        force: If True, ignore cached results

    Returns:
        Dictionary containing benchmark results and metadata
    """
    print("\n=== Starting Benchmark Run ===")
    print(f"Cache directory: {cache_dir}")

    os.makedirs(cache_dir, exist_ok=True)

    start_time = time.time()
    last_status_upload = 0  # Track last status upload time
    results = []
    print("\nRunning benchmarks for all dataset-algorithm combinations...")

    # Use selected datasets/algorithms or fall back to all
    datasets_to_run = selected_datasets if selected_datasets is not None else datasets
    algorithms_to_run = (
        selected_algorithms if selected_algorithms is not None else algorithms
    )

    # Calculate total number of benchmarks
    total_benchmarks = sum(
        1
        for dataset in datasets_to_run
        for algorithm in algorithms_to_run
        if is_compatible(algorithm.tags, dataset.tags)
    )

    # Run benchmarks for each dataset and algorithm combination
    memobin_api_key = os.environ.get("MEMOBIN_API_KEY")
    upload_enabled = os.environ.get("UPLOAD_TO_MEMOBIN") == "1"

    for dataset in datasets_to_run:
        dataset_tags = dataset.tags
        print(f"\n*** Dataset: {dataset.name} (tags: {dataset_tags}) ***")

        # only create the dataset if it is needed
        data = None

        for algorithm in algorithms_to_run:
            alg_name = algorithm.name
            alg_tags = algorithm.tags

            # Skip if algorithm and dataset are not compatible based on tags
            if not is_compatible(alg_tags, dataset_tags):
                if verbose:
                    print(
                        f"\nSkipping algorithm {alg_name} (tags: {alg_tags}) - incompatible with dataset tags"
                    )
                continue

            print(f"\nTesting algorithm: {alg_name} on dataset: {dataset.name}")

            # Upload current status to memobin if enabled (once per minute)
            current_time = time.time()
            if (
                memobin_api_key
                and upload_enabled
                and (current_time - last_status_upload >= 60)
            ):  # Check if 60 seconds have passed
                try:
                    upload_benchmark_status(
                        memobin_api_key,
                        dataset.name,
                        alg_name,
                        results,
                        total_benchmarks,
                        start_time,
                    )
                    last_status_upload = current_time  # Update last upload time
                except Exception as e:
                    print(f"  Warning: Failed to upload status to memobin: {str(e)}")

            # Check if we can use cached result
            cached_result = check_cached_result(
                cache_dir,
                dataset.name,
                alg_name,
                algorithm.version,
                dataset.version,
                system_version,
                force,
                verbose,
            )

            if cached_result is not None:
                print("  Using cached result")
                results.append(cached_result)
                continue

            print(f"  Running benchmark for {alg_name} on {dataset.name}...")
            if data is None:
                data = dataset.create()
                print(f"Created dataset: shape={data.shape}, dtype={data.dtype}")
            else:
                print("Dataset already created")

            # Upload dataset to memobin if enabled
            if memobin_api_key and upload_enabled:
                try:
                    upload_dataset_to_memobin(
                        data,
                        dataset.name,
                        dataset.version,
                        memobin_api_key,
                        cache_dir,
                        verbose,
                    )
                except Exception as e:
                    print(f"  Warning: Failed to upload dataset to memobin: {str(e)}")

            # Run the benchmark
            lossy = "lossy" in alg_tags
            result, encoded = run_compression_benchmark(
                data,
                alg_name,
                algorithm.encode,
                algorithm.decode,
                verbose,
                lossy=lossy
            )

            # Add metadata to result
            result.update(
                {
                    "dataset": dataset.name,
                    "algorithm": alg_name,
                    "algorithm_version": algorithm.version,
                    "dataset_version": dataset.version,
                    "system_version": system_version,
                }
            )
            results.append(result)

            # Save result and compressed data
            save_result_to_cache(
                result,
                encoded,
                cache_dir,
                dataset.name,
                alg_name,
            )
            print(
                f"  Results saved to: {os.path.join(cache_dir, dataset.name, alg_name)}"
            )

            # Upload to memobin if enabled
            if memobin_api_key and upload_enabled:
                try:
                    memobin_url = construct_memobin_url(
                        alg_name,
                        dataset.name,
                        algorithm.version,
                        dataset.version,
                        system_version,
                    )
                    upload_to_memobin(
                        {"result": result},
                        memobin_url,
                        memobin_api_key,
                    )
                    if verbose:
                        print("  Successfully uploaded to memobin")
                except Exception as e:
                    print(f"  Warning: Failed to upload to memobin: {str(e)}")

    print("\n=== Benchmark Run Complete ===\n")

    # Collect algorithm and dataset information
    algorithm_info = collect_algorithm_info(algorithms)
    dataset_info = collect_dataset_info(datasets)

    # Upload final benchmark status
    if memobin_api_key and upload_enabled:
        try:
            upload_benchmark_status(
                memobin_api_key,
                "All datasets",
                "All algorithms",
                results,
                total_benchmarks,
                start_time,
            )
        except Exception as e:
            print(f"  Warning: Failed to upload final status to memobin: {str(e)}")

    return {"results": results, "algorithms": algorithm_info, "datasets": dataset_info}
