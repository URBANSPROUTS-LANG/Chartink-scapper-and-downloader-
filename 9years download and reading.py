import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

SCREENER_URL = "https://chartink.com/screener/short-term-breakouts"
DOWNLOAD_DIR = r"C:\Users\lavanya\Downloads"
WAIT_TIME = 0

chrome_options = Options()
chrome_options.debugger_address = "127.0.0.1:9233"
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

driver = webdriver.Chrome(service=Service(), options=chrome_options)
wait = WebDriverWait(driver, WAIT_TIME)

try:
    print(f"🚀 Opening screener: {SCREENER_URL}")
    driver.get(SCREENER_URL)

    # wait for the backtest section to load
    wait.until(EC.presence_of_element_located((By.ID, "backtest-container")))
    print("Backtest section loaded")

    # open the dropdown scoped inside backtest-container
    backtest = driver.find_element(By.ID, "backtest-container")
    dropdown = backtest.find_element(By.CSS_SELECTOR, "div.custom-dropdown")
    driver.execute_script("arguments[0].click();", dropdown)
    print("Dropdown clicked")
    time.sleep(1)

    # pick the last option (e.g. '9 years')—feel free to target by text if you prefer
    ul = dropdown.find_element(By.CSS_SELECTOR, "ul.multiselectcustom__content")
    options = ul.find_elements(By.CSS_SELECTOR, "li[role='option'] span.multiselectcustom__option")
    driver.execute_script("arguments[0].click();", options[-1])
    print(f"Selected option: {options[-1].text.strip()}")
    time.sleep(2)

    # click “Download csv” and exit
    csv_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[normalize-space(text())='Download csv']")))
    driver.execute_script("arguments[0].scrollIntoView(true);", csv_btn)
    time.sleep(1)
    csv_btn.click()
    print("Download initiated. Waiting a few seconds…")
    time.sleep(5)

finally:
    driver.quit()
    print("Browser closed")
