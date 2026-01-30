#!/usr/bin/env python3
"""
Test script to isolate wavpack lossy compression issue with multi-channel data.
Tests compression ratio for single channel vs all channels with bps=3.
"""

import numpy as np
import requests
import sys
from io import BytesIO

# URL for test data
DATA_URL = "https://tempory.net/ephys-compression-tests/aind/aind_compression_np2_probeB_ch101-110.raw.npy"

def download_data():
    """Download test data from URL."""
    print(f"Downloading data from {DATA_URL}...")
    response = requests.get(DATA_URL)
    response.raise_for_status()
    arr = np.load(BytesIO(response.content))
    print(f"Data shape: {arr.shape}, dtype: {arr.dtype}")
    return arr

def wavpack_encode(x: np.ndarray, bps: float = None) -> bytes:
    """Encode array using WavPack."""
    from wavpack_numcodecs import WavPack
    if bps is not None:
        codec = WavPack(bps=bps)
    else:
        codec = WavPack()
    encoded = codec.encode(x)
    assert isinstance(encoded, bytes)
    return encoded

def test_compression(data: np.ndarray, bps: int = 3):
    """Test compression for single channel vs all channels."""
    
    print(f"\n{'='*60}")
    print(f"Testing WavPack with bps={bps}")
    print(f"{'='*60}\n")
    
    # Test single channel (first channel)
    print("--- Single Channel Test ---")
    single_channel = data[:, 0:1].copy()  # Keep 2D shape (N, 1) and ensure contiguous
    print(f"Single channel shape: {single_channel.shape}")
    print(f"Single channel size: {single_channel.nbytes} bytes")
    
    encoded_single = wavpack_encode(single_channel, bps=bps)
    size_single = len(encoded_single)
    ratio_single = single_channel.nbytes / size_single
    
    print(f"Compressed size: {size_single} bytes")
    print(f"Compression ratio: {ratio_single:.3f}x")
    
    # Test all channels
    print(f"\n--- All Channels Test ---")
    all_channels = np.ascontiguousarray(data)  # Ensure contiguous
    print(f"All channels shape: {all_channels.shape}")
    print(f"All channels size: {all_channels.nbytes} bytes")
    
    encoded_all = wavpack_encode(all_channels, bps=bps)
    size_all = len(encoded_all)
    ratio_all = all_channels.nbytes / size_all
    
    print(f"Compressed size: {size_all} bytes")
    print(f"Compression ratio: {ratio_all:.3f}x")
    
    # Compare
    print(f"\n--- Comparison ---")
    print(f"Single channel compression ratio: {ratio_single:.3f}x")
    print(f"All channels compression ratio: {ratio_all:.3f}x")
    
    # Expected: similar ratios if working correctly
    # If all-channel ratio is much worse, there may be an issue
    if ratio_all < ratio_single * 0.5:
        print(f"\n⚠️  WARNING: All-channel compression ratio is significantly worse!")
        print(f"   This suggests a potential issue with multi-channel compression.")
    elif ratio_all < ratio_single * 0.9:
        print(f"\n⚠️  NOTICE: All-channel compression ratio is somewhat worse.")
    else:
        print(f"\n✓ Compression ratios are similar - working as expected.")
    
    return {
        'single_channel_ratio': ratio_single,
        'all_channels_ratio': ratio_all,
        'single_channel_size': size_single,
        'all_channels_size': size_all
    }

def main():
    """Main test function."""
    try:
        # Download data
        data = download_data()
        
        # Test with bps=3 (the reported issue)
        results = test_compression(data, bps=3)
        
        # Also test with lossless for comparison
        print(f"\n\n{'='*60}")
        print(f"For comparison, testing lossless compression:")
        print(f"{'='*60}\n")
        
        # Lossless single channel
        single_channel = data[:, 0:1].copy()
        encoded_single_lossless = wavpack_encode(single_channel)
        ratio_single_lossless = single_channel.nbytes / len(encoded_single_lossless)
        print(f"Single channel lossless ratio: {ratio_single_lossless:.3f}x")
        
        # Lossless all channels
        all_channels = np.ascontiguousarray(data)
        encoded_all_lossless = wavpack_encode(all_channels)
        ratio_all_lossless = all_channels.nbytes / len(encoded_all_lossless)
        print(f"All channels lossless ratio: {ratio_all_lossless:.3f}x")
        
        print(f"\n{'='*60}")
        print("Test completed successfully!")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
