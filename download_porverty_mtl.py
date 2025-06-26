import os
import time
import shutil
import json

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# AWS imports
import boto3
from botocore.exceptions import NoCredentialsError

# ======== S3 settings ========
s3 = boto3.client('s3')
S3_BUCKET_NAME = 'crime-porverty-heatmap-data-analysis'
S3_INPUT_JSON = 'url-links-poverty/urls-poverty.json'
S3_OUTPUT_LOCAL_JSON = 'data/poverty/urls-poverty.json'
S3_OUTPUT_BUCKET_KEY = 'data/poverty'
S3_FILE_LOCAL_TMP = "downloads"

def get_urls():
    s3.download_file(S3_BUCKET_NAME, S3_INPUT_JSON, S3_OUTPUT_LOCAL_JSON)
    print(f'File downloaded to {S3_OUTPUT_LOCAL_JSON}')

    with open(S3_OUTPUT_LOCAL_JSON, 'r') as file:
        urls = json.load(file)

    return urls

def download_file_from_url(name, url):
    # === Chrome Setup for Headless Downloads ===
    script_dir = os.path.dirname(os.path.abspath(__file__))
    download_path = os.path.join(script_dir, S3_FILE_LOCAL_TMP)
    os.makedirs(download_path, exist_ok=True)

    # === Chrome Setup for Headless Downloads ===
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safeBrowse.enabled": True
    }

    options.add_experimental_option("prefs", prefs)

    # ======== Initialize WebDriver =============
    driver = webdriver.Chrome(options=options)

    # ======== Navigate to page ========
    driver.get(url)

    # ======== Wait for document.readyState ========
    WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")

    # ======== Switch to iframe if present ========
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

    # ======== Wait for the file to be downloaded ========
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
                for _ in range(5):

                    try:
                        current_size = os.path.getsize(file_path)
                    except FileNotFoundError:
                        continue

                    if initial_size == current_size and current_size > 0:
                        downloaded_file = f
                        break
                    initial_size = current_size
                    time.sleep(0.5)
                if downloaded_file:
                    break
        if downloaded_file:
            break
        time.sleep(1)

    # ======== Clean up temporary Chrome files ========
    for f in os.listdir(download_path):
        if f.startswith(".com.google.Chrome.") or f.endswith(".crdownload"):
            try:
                os.remove(os.path.join(download_path, f))

            except OSError as e:
                print(f"Error cleaning up {f}: {e}")


    driver.quit()

    if downloaded_file:
        new_file_name = f"poverty_family_structure_{name}.xlsx"
        local_file_path = os.path.join(download_path, downloaded_file)
        s3_key = os.path.join(S3_OUTPUT_BUCKET_KEY, new_file_name)

        s3 = boto3.client('s3')

        try:
            s3.upload_file(local_file_path, S3_BUCKET_NAME, s3_key)
            print(f"File uploaded to S3: s3://{S3_BUCKET_NAME}/{s3_key}")

            # Delete temporary file after download
            shutil.rmtree(download_path)
        except FileNotFoundError:
            print("The file was not found")
        except NoCredentialsError:
            print("Credentials not available")

if __name__ == "__main__":

    urls = get_urls()

    for url in urls:

        name = url.get("neighbourhood")
        url = url.get("url")

        print("Begin downloading file for neighbourhood:", name)
        download_file_from_url(name, url)
