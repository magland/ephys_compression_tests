from .vyom import datasets as vyom_datasets
from .aind import datasets as aind_datasets
from ..types import Dataset

datasets_list = [
    vyom_datasets,
    aind_datasets,
]

datasets: list[Dataset] = []
for d in datasets_list:
    datasets.extend(d)
