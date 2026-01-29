#!/usr/bin/env python3

import json
import os
from pathlib import Path
from ephys_compression_tests import run_benchmarks
from ephys_compression_tests.run_benchmarks._memobin import upload_to_memobin, construct_memobin_url

def main():
    # Run benchmarks
    print("Running benchmarks...")
    results = run_benchmarks()

    # Save detailed results to JSON
    output_dir = Path("benchmark_results")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "results.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to {output_file}")

    # Upload results to memobin if enabled
    memobin_api_key = os.environ.get("MEMOBIN_API_KEY")
    upload_enabled = os.environ.get("UPLOAD_TO_MEMOBIN") == "1"

    if memobin_api_key and upload_enabled:
        try:
            # Construct URL for the global results file
            url = "https://tempory.net/f/memobin/ephys_compression_tests/global/results.json"
            upload_to_memobin(results, url, memobin_api_key)
            print("Successfully uploaded results to memobin")
        except Exception as e:
            print(f"Warning: Failed to upload results to memobin: {str(e)}")

if __name__ == "__main__":
    main()
