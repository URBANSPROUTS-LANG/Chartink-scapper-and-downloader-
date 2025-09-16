import os
import time
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

SCREENER_URL = "https://chartink.com/screener/short-term-breakouts"
DOWNLOAD_DIR = r"C:\Users\Muthulk\Downloads\chartink_csv"
WAIT_TIME = 30
DOWNLOAD_TIMEOUT = 60

chrome_options = Options()
chrome_options.debugger_address = "127.0.0.1:9233"

prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(), options=chrome_options)
wait = WebDriverWait(driver, WAIT_TIME)

def wait_for_download(directory, timeout=DOWNLOAD_TIMEOUT):
    end_time = time.time() + timeout
    while time.time() < end_time:
        files = glob.glob(os.path.join(directory, "*.csv"))
        if files:
            return max(files, key=os.path.getctime)
        time.sleep(1)
    return None

try:
    print(f"🚀 Opening screener: {SCREENER_URL}")
    driver.get(SCREENER_URL)

    wait.until(EC.presence_of_element_located((By.ID, "backtest-container")))
    print("✅ Backtest section loaded")

    # === Step 1: Find the dropdown container in backtest only ===
    backtest = driver.find_element(By.ID, "backtest-container")
    dropdown_container = backtest.find_element(By.CSS_SELECTOR, "div.custom-dropdown")
    driver.execute_script("arguments[0].click();", dropdown_container)
    print("📂 Dropdown clicked (scoped inside backtest-container)")

    time.sleep(1)  # let it expand

    # === Step 2: Get options ONLY inside this dropdown ===
    ul = dropdown_container.find_element(By.CSS_SELECTOR, "ul.multiselectcustom__content")
    options = ul.find_elements(By.CSS_SELECTOR, "li[role='option'] span.multiselectcustom__option")

    print(f"📋 Found {len(options)} dropdown options:")
    for i, opt in enumerate(options, 1):
        print(f"{i:02d}. '{opt.text.strip()}' (displayed={opt.is_displayed()})")

    # === Step 3: Click '9 years' if available ===
    '''chosen = False
    for opt in options:
        if "9 years" in opt.text:
            driver.execute_script("arguments[0].click();", opt)
            print("✅ Selected 9 years")
            chosen = True
            break
    if not chosen:
        print("❌ '9 years' not found in dropdown")'''

    driver.execute_script("arguments[0].click();", options[-1])

    time.sleep(3)

    # === Step 4: Download CSV ===
    csv_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[normalize-space(text())='Download csv']"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", csv_button)
    time.sleep(1)
    csv_button.click()
    print("📥 Clicked Download CSV... waiting for file")

    downloaded_file = wait_for_download(DOWNLOAD_DIR)
    if downloaded_file:
        print("✅ CSV downloaded:", downloaded_file)
    else:
        print("❌ Download failed or timed out")

finally:
    driver.quit()
    print("🚪 Browser closed")


