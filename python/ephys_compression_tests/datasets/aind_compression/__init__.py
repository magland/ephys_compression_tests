import numpy as np
import os
import requests
import io
from ...types import Dataset

from ..._filters import bandpass_filter


SOURCE_FILE = "aind-compression/__init__.py"


def _load_long_description():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(current_dir, "aind-compression.md")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


LONG_DESCRIPTION = _load_long_description()

tags = ["real", "ecephys", "timeseries", "integer", "correlated"]


def load_aind_np2_probeB_ch101() -> np.ndarray:
    """Load AIND CH101 dataset from external URL.

    Returns:
        Array containing the loaded data
    """
    url = "https://tempory.net/ephys-compression-tests/aind_CH101.raw.npy"
    print(f'Loading AIND dataset from {url}...')
    response = requests.get(url)
    response.raise_for_status()
    data = np.load(io.BytesIO(response.content)).flatten()
    return data

def load_aind_np2_probeB_ch101_110() -> np.ndarray:
    url = "https://tempory.net/ephys-compression-tests/aind/aind_compression_np2_probeB_ch101-110.raw.npy"
    print(f'Loading AIND dataset from {url}...')
    response = requests.get(url)
    response.raise_for_status()
    data = np.load(io.BytesIO(response.content))
    return data

def load_aind_np1_probeA_101_110() -> np.ndarray:
    url = "https://tempory.net/ephys-compression-tests/aind/aind-np1-probeA-ch101-110.raw.npy"
    print(f'Loading AIND dataset from {url}...')
    response = requests.get(url)
    response.raise_for_status()
    data = np.load(io.BytesIO(response.content))
    return data

# ibl-np1-probe00
def load_ibl_np1_probe00_101_110() -> np.ndarray:
    url = "https://tempory.net/ephys-compression-tests/aind/ibl-np1-probe00-ch101-110.raw.npy"
    print(f'Loading IBL dataset from {url}...')
    response = requests.get(url)
    response.raise_for_status()
    data = np.load(io.BytesIO(response.content))
    return data

dataset_dicts_base = [
    {
        "name": "aind-compression-np2-ProbeB-ch101",
        "version": "1",
        "description": "AIND CH101 dataset",
        "create": load_aind_np2_probeB_ch101,
        "tags": tags + ["single-channel"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "aind-compression-np2-ProbeB-ch101-110",
        "version": "1",
        "description": "AIND CH101-110 dataset",
        "create": load_aind_np2_probeB_ch101_110,
        "tags": tags + ["multi-channel"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "aind-compression-np1-ProbeA-ch101-110",
        "version": "1",
        "description": "AIND NP1 ProbeA CH101-110 dataset",
        "create": load_aind_np1_probeA_101_110,
        "tags": tags + ["multi-channel"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "ibl-compression-np1-Probe00-ch101-110",
        "version": "1",
        "description": "IBL NP1 Probe00 CH101-110 dataset",
        "create": load_ibl_np1_probe00_101_110,
        "tags": tags + ["multi-channel"],
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
        filtered = bandpass_filter(data, sampling_frequency=30000, lowcut=300, highcut=4000)
        filtered = filtered.astype(data.dtype)
        return filtered

    dataset_dicts.append(
        {
            "name": f'{d["name"]}-filtered',
            "version": "1",
            "description": f'{d["description"]} (bandpass filtered 300-4000 Hz)',
            "create": create0,
            "tags": d["tags"] + ["filtered", "bandpass"],
            "source_file": SOURCE_FILE,
            "long_description": LONG_DESCRIPTION,
        }
    )


datasets = [Dataset(**a) for a in dataset_dicts]
