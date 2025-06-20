from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


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

def test_page():
    driver.get(url)

    # Wait for document.readyState == complete
    WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")
    print("Page fully loaded according to readyState.")

    # Check if inside iframe, switch if needed (example for first iframe)
    try:
        iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
        print("Switched to iframe.")
    except Exception:
        print("No iframe found or switch not needed.")

    # Wait for your element by ID or use alternative selector
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "resource-eb255cf4-128c-4840-bb9a-a01e2b84333c"))
    )
    print("✅ Waited for page to load.")

test_page()

try:
    accept_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "cky-btn-accept"))
    )
    accept_button.click()
    print("✅ Cookie banner accepted.")
except Exception as e:
    print("⚠️ Cookie banner not found or already accepted:", e)

# === Wait until body loads ===
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.ID, "resource-eb255cf4-128c-4840-bb9a-a01e2b84333c"))
)

print("✅ Waited for page to load.")

download_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable(
        (By.XPATH, '//button[contains(@onclick, "downloadXLSX(\'csv_generale_33\'")]')
    )
)
driver.execute_script("arguments[0].scrollIntoView();", download_button)
download_button.click()
print("✅ Download button clicked.")

# === Wait for download to complete (adjust if needed) ===
time.sleep(10)

# Optional: Verify what was downloaded
downloaded_files = os.listdir("/tmp/downloads")
print("Downloaded files:", downloaded_files)

# === Quit browser ===
driver.quit()
