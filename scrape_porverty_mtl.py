from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

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
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

# === Ensure download folder exists ===
os.makedirs("/tmp/downloads", exist_ok=True)

# === Initialize WebDriver ===
driver = webdriver.Chrome(options=options)

# === Navigate to page ===
url = "https://donnees.montreal.ca/dataset/portrait-thematique-sur-la-pauvrete-2021/resource/eb255cf4-128c-4840-bb9a-a01e2b84333c"
driver.get(url)

def test_page():

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

    # Use download button
    download_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@onclick, \"downloadXLSX('csv_generale_33'\")]")
            )
        )

    driver.execute_script("arguments[0].scrollIntoView();", download_button)
    download_button.click()

    print("Files in downloads dir after download:", os.listdir(download_path))

    driver.quit()



