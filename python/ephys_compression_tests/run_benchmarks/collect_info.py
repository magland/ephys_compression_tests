from typing import List, Dict, Any
from ._memobin import construct_dataset_url
from ..types import Algorithm

GITHUB_ALGORITHMS_PREFIX = "https://github.com/magland/ephys_compression_tests/blob/main/python/ephys_compression_tests/algorithms/"
GITHUB_DATASETS_PREFIX = "https://github.com/magland/ephys_compression_tests/blob/main/python/ephys_compression_tests/datasets/"


def collect_algorithm_info(algorithms: List[Dict[str, Algorithm]]) -> List[Dict[str, Any]]:
    """Collect information about compression algorithms.

    Args:
        algorithms: List of algorithm dictionaries

    Returns:
        List of algorithm information dictionaries
    """
    algorithm_info = []
    for algorithm in algorithms:
        info = {
            "name": algorithm.name,
            "description": algorithm.description if algorithm.description else "",
            "long_description": algorithm.long_description if algorithm.long_description else "",
            "version": algorithm.version,
            "tags": algorithm.tags if algorithm.tags else [],
        }
        if algorithm.source_file:
            info["source_file"] = GITHUB_ALGORITHMS_PREFIX + algorithm.source_file
        algorithm_info.append(info)
    return algorithm_info


def collect_dataset_info(datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collect information about benchmark datasets.

    Args:
        datasets: List of dataset dictionaries

    Returns:
        List of dataset information dictionaries
    """
    dataset_info = []
    for dataset in datasets:
        info = {
            "name": dataset.name,
            "description": dataset.description if dataset.description else "",
            "long_description": dataset.long_description if dataset.long_description else "",
            "version": dataset.version,
            "tags": dataset.tags if dataset.tags else [],
            "data_url_raw": construct_dataset_url(
                dataset.name, dataset.version, "dat"
            ),
            "data_url_npy": construct_dataset_url(
                dataset.name, dataset.version, "npy"
            ),
            "data_url_json": construct_dataset_url(
                dataset.name, dataset.version, "json"
            ),
        }
        if dataset.source_file:
            info["source_file"] = GITHUB_DATASETS_PREFIX + dataset.source_file
        dataset_info.append(info)
    return dataset_info
