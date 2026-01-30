import os
import spikeinterface as si
import numpy as np
from s3_utils import download_s3_folder

s3_base_url = "s3://aind-benchmark-data/ephys-compression/"

folder_names = [
    ("aind-np2/612962_2022-04-13_19-18-04_ProbeB", "aind-np2-probeB"),
    ("aind-np1/625749_2022-08-03_15-15-06_ProbeA", "aind-np1-probeA")
]

for folder_name, name0 in folder_names:
    s3_folder_name = f"{s3_base_url}/{folder_name}"
    local_folder_name = f"{folder_name}.si"

    if not os.path.exists(local_folder_name):
        # make parent directories if needed
        os.makedirs(os.path.dirname(local_folder_name), exist_ok=True)
        print(f'Downloading {s3_folder_name} to {local_folder_name}...')
        download_s3_folder(s3_folder_name, local_folder_name)

    recording = si.load(
        local_folder_name
    )

    channel_ids = [
        'CH101',
        'CH102',
        'CH103',
        'CH104',
        'CH105',
        'CH106',
        'CH107',
        'CH108',
        'CH109',
        'CH110'
    ]

    fname = f'{name0}-ch101-110.raw.npy'
    if not os.path.exists(fname):
        print(f'Writing {fname}...')
        X = recording.get_traces(channel_ids=channel_ids, start_frame=30000, end_frame=30000 + 30000 * 10)
        print(f'X.shape = {X.shape}')
        np.save(fname, X)
