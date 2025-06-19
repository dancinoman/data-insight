from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import boto3

# === Chrome Setup for Headless Downloads ===
options = Options()
options.add_argument("--headless=new")  # <-- Use the updated headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
prefs = {"download.default_directory": "/tmp/downloads"}
options.add_experimental_option("prefs", prefs)

# === Ensure download folder exists ===
os.makedirs("/tmp/downloads", exist_ok=True)

# === Initialize WebDriver ===
driver = webdriver.Chrome(options=options)

# === Navigate to page ===
url = "https://donnees.montreal.ca/dataset/portrait-thematique-sur-la-pauvrete-2021/resource/eb255cf4-128c-4840-bb9a-a01e2b84333c"
driver.get(url)

# Debug page loading so far
time.sleep(5)
print(driver.page_source[:1000])

# === Wait until body loads ===
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.TAG_NAME, "body"))
)

# === Wait for the correct download button ===
download_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (By.XPATH,'//button[contains(@onclick, "downloadXLSX")]')
    )
)

# === Click to download ===
download_button.click()

# === Wait for download to complete (adjust if needed) ===
time.sleep(10)

# Optional: Verify what was downloaded
downloaded_files = os.listdir("/tmp/downloads")
print("Downloaded files:", downloaded_files)

# === Quit browser ===
driver.quit()
