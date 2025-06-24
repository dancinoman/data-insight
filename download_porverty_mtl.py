from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import shutil

import boto3
from botocore.exceptions import NoCredentialsError

# === Chrome Setup for Headless Downloads ===
script_dir = os.path.dirname(os.path.abspath(__file__))
download_path = os.path.join(script_dir, "downloads")
os.makedirs(download_path, exist_ok=True)

# === Chrome Setup for Headless Downloads ===
options = Options()
options.add_argument("--headless=new")  # <-- Use the updated headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
prefs = {
    "download.default_directory": download_path,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safeBrowse.enabled": True
}
options.add_experimental_option("prefs", prefs)

# === Initialize WebDriver ===
driver = webdriver.Chrome(options=options)

# === Navigate to page ===
url = "https://donnees.montreal.ca/dataset/portrait-thematique-sur-la-pauvrete-2021/resource/eb255cf4-128c-4840-bb9a-a01e2b84333c"
driver.get(url)

# Wait for document.readyState == complete
WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")

# Check if inside iframe, switch if needed (example for first iframe)
try:
    iframe = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
    )
    driver.switch_to.frame(iframe)
except Exception:
    print("No iframe found or switch not needed.")

# Get initial list of files in the download directory
initial_files = set(os.listdir(download_path))

# Use download button
download_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@onclick, \"downloadXLSX('csv_generale_33'\")]")
        )
    )

driver.execute_script("arguments[0].scrollIntoView();", download_button)
download_button.click()

print("Download button clicked. Waiting for file to appear...")

# === Wait for the file to be downloaded ===
# This loop waits until a new file appears in the directory that is not a temporary Chrome file
# and its size stops changing, indicating the download is complete.
downloaded_file = None
timeout = 60  # seconds
start_time = time.time()

while time.time() - start_time < timeout:
    current_files = set(os.listdir(download_path))
    new_files = current_files - initial_files

    for f in new_files:
        file_path = os.path.join(download_path, f)
        # Exclude Chrome's temporary download files and check for actual files
        if not f.startswith(".com.google.Chrome.") and not f.endswith(".crdownload"):
            # Check if the file size is stable (download complete)
            initial_size = -1
            for _ in range(5):  # Check size 5 times with a small delay
                current_size = os.path.getsize(file_path)
                if initial_size == current_size and current_size > 0:
                    downloaded_file = f
                    break
                initial_size = current_size
                time.sleep(0.5)
            if downloaded_file:
                break
    if downloaded_file:
        break
    time.sleep(1) # Wait a bit before re-checking

# === Clean up temporary Chrome files ===
for f in os.listdir(download_path):
    if f.startswith(".com.google.Chrome.") or f.endswith(".crdownload"):
        try:
            os.remove(os.path.join(download_path, f))
            print(f"Cleaned up temporary file: {f}")
        except OSError as e:
            print(f"Error cleaning up {f}: {e}")

print("Files in downloads dir after processing:", os.listdir(download_path))

driver.quit()

# === Upload to S3 ===
s3_bucket_name = 'crime-porverty-heatmap-data-analysis'
s3_key_prefix = 'data/poverty/'

if downloaded_file:
    new_file_name = "poverty_family_structure.xlsx"
    local_file_path = os.path.join(download_path, downloaded_file)
    s3_key = os.path.join(s3_key_prefix, new_file_name)

    s3 = boto3.client('s3')

    try:
        s3.upload_file(local_file_path, s3_bucket_name, s3_key)
        print(f"File uploaded to S3: s3://{s3_bucket_name}/{s3_key}")

        # Delete temporary file after download
        shutil.rmtree(download_path)
        print(f"Temporary file deleted: {local_file_path}")
        print("Script completed successfully.")
    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")
