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


# It's important to correct the quantization levels before using these datasets
# Wavpack in particular will do a lot worse if the data is not properly quantized
def correct_quantization_for_channel(data: np.ndarray) -> np.ndarray:
    closed_to_zero_val = np.argmin(np.abs(data))
    print(f'Value closest to zero: {data[closed_to_zero_val]} at index {closed_to_zero_val}')
    data = data - data[closed_to_zero_val]
    unique_vals = np.unique(data)
    # differences between unique values
    diffs = np.diff(unique_vals)
    # minimum diff is the quantization step size
    diff0 = np.min(diffs[diffs > 0])
    print(f'Identified quantization step size: {diff0}')
    # divide by quantization step size
    data = data / diff0
    data = data.astype(np.int16)
    return data

def correct_quantization(data: np.ndarray) -> np.ndarray:
    if data.ndim == 1:
        return correct_quantization_for_channel(data)
    elif data.ndim == 2:
        corrected_channels = []
        for ch in range(data.shape[1]):
            print(f'Correcting quantization for channel {ch}...')
            corrected_ch = correct_quantization_for_channel(data[:, ch])
            corrected_channels.append(corrected_ch)
        return np.stack(corrected_channels, axis=1)
    else:
        raise ValueError(f'Unsupported data ndim: {data.ndim}')

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
    data = correct_quantization(data)
    return data

def load_aind_np2_probeB_ch101_110() -> np.ndarray:
    url = "https://tempory.net/ephys-compression-tests/aind/aind_compression_np2_probeB_ch101-110.raw.npy"
    print(f'Loading AIND dataset from {url}...')
    response = requests.get(url)
    response.raise_for_status()
    data = np.load(io.BytesIO(response.content))
    data = correct_quantization(data)
    return data

def load_aind_np1_probeA_101_110() -> np.ndarray:
    url = "https://tempory.net/ephys-compression-tests/aind/aind-np1-probeA-ch101-110.raw.npy"
    print(f'Loading AIND dataset from {url}...')
    response = requests.get(url)
    response.raise_for_status()
    data = np.load(io.BytesIO(response.content))
    data = correct_quantization(data)
    return data

# ibl-np1-probe00
def load_ibl_np1_probe00_101_110() -> np.ndarray:
    url = "https://tempory.net/ephys-compression-tests/aind/ibl-np1-probe00-ch101-110.raw.npy"
    print(f'Loading IBL dataset from {url}...')
    response = requests.get(url)
    response.raise_for_status()
    data = np.load(io.BytesIO(response.content))
    data = correct_quantization(data)
    return data

dataset_dicts_base = [
    {
        "name": "aind-compression-np2-ProbeB-ch101",
        "version": "2",
        "description": "AIND CH101 dataset",
        "create": load_aind_np2_probeB_ch101,
        "tags": tags + ["single-channel"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "aind-compression-np2-ProbeB-ch101-110",
        "version": "2",
        "description": "AIND CH101-110 dataset",
        "create": load_aind_np2_probeB_ch101_110,
        "tags": tags + ["multi-channel"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "aind-compression-np1-ProbeA-ch101-110",
        "version": "2",
        "description": "AIND NP1 ProbeA CH101-110 dataset",
        "create": load_aind_np1_probeA_101_110,
        "tags": tags + ["multi-channel"],
        "source_file": SOURCE_FILE,
        "long_description": LONG_DESCRIPTION,
    },
    {
        "name": "ibl-compression-np1-Probe00-ch101-110",
        "version": "2",
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
            "version": "2",
            "description": f'{d["description"]} (bandpass filtered 300-4000 Hz)',
            "create": create0,
            "tags": d["tags"] + ["filtered", "bandpass"],
            "source_file": SOURCE_FILE,
            "long_description": LONG_DESCRIPTION,
        }
    )

# Add common-mode corrected versions
# Oddly enough, this didn't seem to help compression much, so leave it commented out for now
# for d in dataset_dicts_base:
#     if "multi-channel" in d["tags"]:
#         def create1(d=d) -> np.ndarray:
#             data = d["create"]()
#             median_signal = np.median(data, axis=1)
#             # now create a new array where the first channel is the median
#             # and the rest are the original channels minus the median
#             # but we exclude the last channel because it can be recovered
#             new_data = np.zeros_like(data)
#             new_data[:, 0] = median_signal
#             for ch in range(1, data.shape[1]):
#                 new_data[:, ch] = data[:, ch] - median_signal
#             return new_data
#         dataset_dicts.append(
#             {
#                 "name": f'{d["name"]}-cmc',
#                 "version": "1",
#                 "description": f'{d["description"]} (common-mode corrected)',
#                 "create": create1,
#                 "tags": d["tags"] + ["common-mode-corrected"],
#                 "source_file": SOURCE_FILE,
#                 "long_description": LONG_DESCRIPTION,
#             }
#         )


datasets = [Dataset(**a) for a in dataset_dicts]
