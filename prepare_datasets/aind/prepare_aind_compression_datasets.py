import os
import spikeinterface as si
import numpy as np
from s3_utils import download_s3_folder

s3_base_url = "s3://aind-benchmark-data/ephys-compression"

folder_names = [
    # ("aind-np2/612962_2022-04-13_19-18-04_ProbeB", "aind-np2-probeB", "CH"),
    # ("aind-np1/625749_2022-08-03_15-15-06_ProbeA", "aind-np1-probeA", "AP")
    ("ibl-np1/CSHZAD026_2020-09-04_probe00", "ibl-np1-probe00", "AP"),
]

for folder_name, name0, channel_prefix in folder_names:
    s3_folder_name = f"{s3_base_url}/{folder_name}"
    local_folder_name = f"{folder_name}.si"

    if not os.path.exists(local_folder_name):
        # make parent directories if needed
        os.makedirs(os.path.dirname(local_folder_name), exist_ok=True)
        print(f'Downloading {s3_folder_name} to {local_folder_name}...')
        # IMPORTANT NOTE: we may interrupt this download early because we really only need the first part.
        download_s3_folder(s3_folder_name, local_folder_name)

    # For now this only works with spikeinterface 0.102
    recording = si.load(
        local_folder_name
    )

    channel_ids = [
        f'{channel_prefix}101',
        f'{channel_prefix}102',
        f'{channel_prefix}103',
        f'{channel_prefix}104',
        f'{channel_prefix}105',
        f'{channel_prefix}106',
        f'{channel_prefix}107',
        f'{channel_prefix}108',
        f'{channel_prefix}109',
        f'{channel_prefix}110'
    ]

    fname = f'{name0}-ch101-110.raw.npy'
    if not os.path.exists(fname):
        print(f'Writing {fname}...')
        X = recording.get_traces(channel_ids=channel_ids, start_frame=30000, end_frame=30000 + 30000 * 10)
        print(f'X.shape = {X.shape}')
        np.save(fname, X)
