import numpy as np
import os
import requests
import io
from ...types import Dataset

from ..._filters import bandpass_filter


SOURCE_FILE = "vyom/__init__.py"


def _load_long_description():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(current_dir, "vyom.md")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


LONG_DESCRIPTION = _load_long_description()

tags = ["real", "ecephys", "timeseries", "1d", "integer", "correlated"]


def load_vyom_example_ch0_seg2_6() -> np.ndarray:
    """Load Vyom example dataset from external URL.

    Returns:
        Array containing the loaded data
    """
    url = "https://tempory.net/ephys-compression-tests/vyom_example_ch0_seg2-6.npy"
    print(f'Loading Vyom example dataset from {url}...')
    response = requests.get(url)
    response.raise_for_status()
    data = np.load(io.BytesIO(response.content))
    return data
    


dataset_dicts_base = [
    {
        "name": "vyom-example-ch0-seg2-6",
        "version": "1",
        "description": "Vyom example dataset",
        "create": load_vyom_example_ch0_seg2_6,
        "tags": tags,
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    }
]

dataset_dicts = []
for d in dataset_dicts_base:
    dataset_dicts.append(d)

# Add filtered versions
for d in dataset_dicts_base:
    def create0(d=d) -> np.ndarray:
        data = d["create"]()
        filtered = bandpass_filter(data, sampling_frequency=20000, lowcut=300, highcut=4000)
        filtered = filtered.astype(data.dtype)
        return filtered

    dataset_dicts.append(
        {
            "name": f'{d["name"]}-bandpass',
            "version": "1",
            "description": f'{d["description"]} (bandpass filtered 300-4000 Hz)',
            "create": create0,
            "tags": d["tags"] + ["filtered", "bandpass"],
            "source_file": SOURCE_FILE,
            "long_description": LONG_DESCRIPTION,
        }
    )


datasets = [Dataset(**a) for a in dataset_dicts]
