# data_loader.py
import os
import time
import logging
import gdown
from pathlib import Path

# ----------------------------
# CONFIG
# ----------------------------
FOLDER_URL = "https://drive.google.com/drive/folders/1-fC3EKyPfzX1vry8G0mQ8Unyeq8p-adx"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# ----------------------------
# SETUP LOGGING
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


# ----------------------------
# HELPERS
# ----------------------------
def get_project_root():
    """
    Returns the project root path (where run_pipeline.py or data folder exists)
    """
    current_path = Path.cwd()  # start from current working directory
    while current_path != current_path.parent:
        if (current_path / "run_pipeline.py").exists() or (current_path / "data").exists():
            return current_path
        current_path = current_path.parent
    # fallback to current working directory
    return Path.cwd()


def download_data(folder_url=FOLDER_URL, output_folder=None, max_retries=MAX_RETRIES):
    if output_folder is None:
        project_root = get_project_root()
        output_folder = project_root / "data"
    output_folder.mkdir(parents=True, exist_ok=True)

    attempt = 0
    while attempt < max_retries:
        try:
            logging.info(f"Starting download attempt {attempt + 1} to {output_folder}...")
            gdown.download_folder(folder_url, output=str(output_folder), quiet=False)
            logging.info("Download completed successfully.")
            return True
        except Exception as e:
            attempt += 1
            logging.warning(f"Download failed: {e}. Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
    logging.error("Failed to download data after multiple attempts.")
    return False


# ----------------------------
# MAIN FUNCTION
# ----------------------------
def load_data(force_update=False):
    """
    Ensures the 'data/' folder exists in the project root and is populated.

    Args:
        force_update (bool): If True, downloads data even if folder exists.
    """
    project_root = get_project_root()
    data_folder = project_root / "data"

    if force_update or not data_folder.exists() or not any(data_folder.iterdir()):
        logging.info(f"Data folder missing or empty at {data_folder}. Downloading...")
        success = download_data(output_folder=data_folder)
        if success:
            logging.info("Data downloaded successfully.")
        else:
            logging.error("Failed to download data.")
    else:
        logging.info(f"Data folder already exists at {data_folder}. Skipping download.")

    # Return list of files for convenience
    files = [str(f) for f in data_folder.iterdir()]
    return files


# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    files = load_data()
    logging.info(f"Data files available: {files}")