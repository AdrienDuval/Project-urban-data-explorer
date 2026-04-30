# data_loader.py
import time
import logging
import gdown
from src.config import BRONZE

# ----------------------------
# CONFIG
# ----------------------------
# Each entry: (subfolder name under bronze/, Drive folder URL)
BRONZE_SUBFOLDERS = [
    ("main_data",                   "https://drive.google.com/drive/folders/1WkfU2mNs19nhgsfK-qoho74RaCcNj08y"),
    ("indice_vivabilite_familiale", "https://drive.google.com/drive/folders/1F9m1BrjhrhE5Awm2H6bPpd5IJ3FjRqLx"),
    ("public_service_data",         "https://drive.google.com/drive/folders/1Tf8FMyGvAL7cVSYLdR8E5GTf-mCXhCJe"),
    ("transport_data",              "https://drive.google.com/drive/folders/1V7ZdJ6qNzilavQW3XUmA0q66rqW9UYTk"),
    ("indice_confort_thermique",    "https://drive.google.com/drive/folders/1E3yOCO4fL3r3JFRBvcOihwXc0k3NnSzt"),
    ("sale_price_data",             "https://drive.google.com/drive/folders/1vAFfqW9262i6Jj5X9GxIBNkRg3kRLk6a"),
    ("rent_data",                   "https://drive.google.com/drive/folders/1OipyPvX6jBDSevbrrdykSKPJDe58xFlt"),
    ("demographics",                "https://drive.google.com/drive/folders/1SuMkne_Pmokv6zSiHZv3-6FDllNLiGcV")
]

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


def _download_subfolder(name, url, max_retries=MAX_RETRIES):
    target = BRONZE / name
    if target.exists() and any(target.iterdir()):
        logging.info("Skipping '%s' — already populated.", name)
        return True

    target.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, max_retries + 1):
        try:
            logging.info("Downloading '%s' (attempt %d)...", name, attempt)
            gdown.download_folder(url, output=str(target), quiet=False)
            logging.info("'%s' downloaded successfully.", name)
            return True
        except Exception as e:
            logging.warning("Failed to download '%s': %s. Retrying in %ds...", name, e, RETRY_DELAY)
            time.sleep(RETRY_DELAY)

    logging.error("Could not download '%s' after %d attempts.", name, max_retries)
    return False


# ----------------------------
# MAIN FUNCTION
# ----------------------------
def load_data(force_update=False):
    """
    Ensures each bronze subfolder exists and is populated from Google Drive.

    Args:
        force_update (bool): If True, re-downloads even if folders already exist.
    """
    BRONZE.mkdir(parents=True, exist_ok=True)

    if force_update:
        import shutil
        shutil.rmtree(BRONZE)
        BRONZE.mkdir(parents=True, exist_ok=True)

    all_ok = True
    for name, url in BRONZE_SUBFOLDERS:
        ok = _download_subfolder(name, url)
        all_ok = all_ok and ok

    if all_ok:
        logging.info("All bronze subfolders ready.")
    else:
        logging.error("Some subfolders failed to download — check logs above.")

# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    load_data()