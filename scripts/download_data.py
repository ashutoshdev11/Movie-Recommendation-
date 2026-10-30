"""
Download and extract the MovieLens 100K dataset from GroupLens.
Strictly extracts to data/raw/ and validates file presence.
"""

import os
import sys
import zipfile
import requests

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
TARGET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
EXPECTED_FILES = [
    "u.data",
    "u.item",
    "u.user",
    "u.genre",
    "u.occupation",
    "u.info",
]


def download_and_extract(url: str = MOVIELENS_URL, target_dir: str = TARGET_DIR) -> None:
    os.makedirs(target_dir, exist_ok=True)
    zip_path = os.path.join(target_dir, "ml-100k.zip")

    # Check if files already extracted
    all_present = all(os.path.exists(os.path.join(target_dir, "ml-100k", f)) for f in EXPECTED_FILES)
    if all_present:
        print(f"Dataset already downloaded and extracted in {os.path.join(target_dir, 'ml-100k')}.")
        return

    print(f"Downloading MovieLens 100K from {url}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, stream=True, timeout=30)
    response.raise_for_status()

    with open(zip_path, "wb") as out_file:
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                out_file.write(chunk)

    print(f"Downloaded {os.path.getsize(zip_path)} bytes to {zip_path}.")

    print("Extracting archive...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(target_dir)

    # Clean up zip archive to avoid duplicate disk usage
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # Validate presence of expected files
    dataset_folder = os.path.join(target_dir, "ml-100k")
    for f in EXPECTED_FILES:
        fp = os.path.join(dataset_folder, f)
        if not os.path.exists(fp):
            raise FileNotFoundError(f"Expected dataset file not found: {fp}")

    print("Dataset successfully extracted and verified:")
    for f in EXPECTED_FILES:
        size = os.path.getsize(os.path.join(dataset_folder, f))
        print(f" - {f}: {size} bytes")


if __name__ == "__main__":
    download_and_extract()
