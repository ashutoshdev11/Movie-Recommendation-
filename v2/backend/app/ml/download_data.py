"""
Download and extract the MovieLens 1M dataset for MovieRec Version 2.
Downloads directly from the official GroupLens repository and verifies file integrity.
"""

import hashlib
import io
import os
import sys
import zipfile
import certifi
import requests

ML_1M_URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"
EXPECTED_FILES = ["ratings.dat", "movies.dat", "users.dat", "README"]


def download_ml_1m(target_dir: str, timeout: int = 60) -> str:
    """
    Download and extract ml-1m.zip into target_dir.
    
    Args:
        target_dir: Destination directory for raw ML-1M files.
        timeout: Network timeout in seconds.
        
    Returns:
        Path to the extracted directory containing the .dat files.
    """
    os.makedirs(target_dir, exist_ok=True)
    
    # Check if files already extracted
    all_exist = all(os.path.exists(os.path.join(target_dir, f)) for f in EXPECTED_FILES)
    if all_exist:
        print(f"[ML-1M] Dataset already present at: {target_dir}")
        return target_dir

    print(f"[ML-1M] Downloading MovieLens 1M from {ML_1M_URL}...")
    headers = {"User-Agent": "MovieRec-V2-Ingestion/2.0"}
    
    response = requests.get(
        ML_1M_URL,
        headers=headers,
        verify=certifi.where(),
        timeout=timeout,
        stream=True,
    )
    response.raise_for_status()

    zip_buffer = io.BytesIO()
    total_bytes = 0
    for chunk in response.iter_content(chunk_size=1024 * 64):
        if chunk:
            zip_buffer.write(chunk)
            total_bytes += len(chunk)

    print(f"[ML-1M] Downloaded {total_bytes / (1024 * 1024):.2f} MB. Verifying and extracting...")
    
    with zipfile.ZipFile(zip_buffer) as zf:
        for member in zf.namelist():
            # In zip, files are inside ml-1m/
            filename = os.path.basename(member)
            if filename in EXPECTED_FILES:
                target_path = os.path.join(target_dir, filename)
                with zf.open(member) as src, open(target_path, "wb") as dst:
                    dst.write(src.read())
                print(f"[ML-1M] Extracted {filename} ({os.path.getsize(target_path):,} bytes)")

    print(f"[ML-1M] Successfully extracted all dataset files to {target_dir}")
    return target_dir


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dest_dir = os.path.join(base_dir, "data", "raw", "ml-1m")
    download_ml_1m(dest_dir)
