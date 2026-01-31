from .retina512 import datasets as retina512_datasets
from .aind_compression import datasets as aind_compression_datasets
from ..types import Dataset

datasets_list = [
    retina512_datasets,
    aind_compression_datasets,
]

datasets: list[Dataset] = []
for d in datasets_list:
    datasets.extend(d)
