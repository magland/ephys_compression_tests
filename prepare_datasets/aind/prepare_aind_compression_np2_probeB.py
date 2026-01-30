import os
import spikeinterface as si
import numpy as np
from s3_utils import download_s3_folder

s3_folder_name = "s3://aind-benchmark-data/ephys-compression/aind-np2/612962_2022-04-13_19-18-04_ProbeB"
local_folder_name = "612962_2022-04-13_19-18-04_ProbeB.si"

if not os.path.exists(local_folder_name):
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

fname = f'aind_compression_np2_probeB_ch101-110.raw.npy'
if not os.path.exists(fname):
    print(f'Writing {fname}...')
    X = recording.get_traces(channel_ids=channel_ids, start_frame=30000, end_frame=30000 + 30000 * 10)
    print(f'X.shape = {X.shape}')
    np.save(fname, X)
