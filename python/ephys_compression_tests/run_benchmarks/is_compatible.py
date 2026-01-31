from typing import List


def is_compatible(algorithm_tags: List[str], dataset_tags: List[str]) -> bool:
    """Check if an algorithm is compatible with a dataset based on their tags.

    Args:
        algorithm_tags: List of tags for the algorithm
        dataset_tags: List of tags for the dataset

    Returns:
        True if the algorithm should be applied to the dataset
    """
    # If algorithm has delta_encoding or lpc_prediction, dataset must have continuous, timeseries, 1d, integer
    if "delta_encoding" in algorithm_tags or "lpc_prediction" in algorithm_tags:
        if (
            "correlated" not in dataset_tags
            or "timeseries" not in dataset_tags
            or "1d" not in dataset_tags
            or "integer" not in dataset_tags
        ):
            return False

    # If algorithm has zero_rle, dataset must have sparse, timeseries, 1d
    if "zero_rle" in algorithm_tags:
        if (
            "sparse" not in dataset_tags
            or "timeseries" not in dataset_tags
            or "1d" not in dataset_tags
        ):
            return False

    # If algorithm has integer, dataset must have integer
    if "integer" in algorithm_tags:
        if "integer" not in dataset_tags:
            return False

    # If algorithm has "no_bernoulli", dataset must not have "bernoulli"
    if "no_bernoulli" in algorithm_tags:
        if "bernoulli" in dataset_tags:
            return False

    return True
