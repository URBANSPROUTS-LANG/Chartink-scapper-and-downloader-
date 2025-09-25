import os
import time
import glob
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
import re

# Configuration
LINKS_FILE = r"C:\Users\Muthulk\Downloads\1.txt"
DOWNLOAD_DIR = r"C:\Users\Muthulk\Downloads"
DEFAULT_DOWNLOADS = r"C:\Users\Muthulk\Downloads"
WAIT_TIME = 0
DOWNLOAD_TIMEOUT = 60  # wait up to 30 seconds for CSV
LOG_FILE = r"C:\Users\Muthulk\Downloads\chartink_log.txt"
CSV_LOG_FILE = r"C:\Users\Muthulk\Downloads\chartink_downloads.csv"

# === Logging Setup ===
class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")  # overwrite each run
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger(LOG_FILE)

# Chrome options
chrome_options = Options()
chrome_options.debugger_address = "127.0.0.1:9233"
prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

def log_download(url, filename):
    """Append URL + original downloaded filename into CSV"""
    try:
        with open(CSV_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{url},{filename}\n")
    except Exception as e:
        print(f"⚠️ Could not write to CSV log: {e}")

def read_links_from_file(filename):
    links = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('http'):
                        links.append(line)
                    else:
                        print(f"⚠️  Line {line_num}: Invalid URL format - {line}")
        return links
    except FileNotFoundError:
        print(f"File '{filename}' not found!")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def wait_for_download(primary_dir, fallback_dir, timeout=DOWNLOAD_TIMEOUT):
    """Wait for CSV file to appear in primary directory"""
    print(f"Monitoring directories:")
    print(f"   Primary: {primary_dir}")
    
    end_time = time.time() + timeout
    initial_files = set(glob.glob(os.path.join(primary_dir, "*.csv")))
    
    while time.time() < end_time:
        current_files = set(glob.glob(os.path.join(primary_dir, "*.csv")))
        new_files = current_files - initial_files
        if new_files:
            latest_file = max(new_files, key=os.path.getctime)
            print(f"New CSV detected: {os.path.basename(latest_file)}")
            return latest_file
        time.sleep(0.5)
    
    print("=Download timeout reached")
    # Fallback: return newest CSV anyway if any
    csv_files = glob.glob(os.path.join(primary_dir, "*.csv"))
    if csv_files:
        latest_file = max(csv_files, key=os.path.getctime)
        print(f"Returning latest CSV anyway: {os.path.basename(latest_file)}")
        return latest_file
    return None

def sanitize_filename(url):
    path = urlparse(url).path
    screener_name = path.split('/')[-1] if path.split('/')[-1] else 'screener'
    return re.sub(r'[^\w\-_]', '_', screener_name)

def process_screener(driver, wait, url, screener_num, total_screeners):
    print(f"\n{'='*60}")
    print(f"Processing screener {screener_num}/{total_screeners}")
    print(f" URL: {url}")
    
    try:
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.ID, "backtest-container")))
        print("Backtest section loaded")
        
        backtest = driver.find_element(By.ID, "backtest-container")
        dropdown_container = backtest.find_element(By.CSS_SELECTOR, "div.custom-dropdown")
        driver.execute_script("arguments[0].click();", dropdown_container)
        print("Dropdown clicked (scoped inside backtest-container)")
        time.sleep(1)
        
        print("Waiting for dropdown options to load...")
        time.sleep(2)
        
        # Get dropdown options
        options = []
        for attempt in range(3):
            try:
                ul = dropdown_container.find_element(By.CSS_SELECTOR, "ul.multiselectcustom__content")
                options = ul.find_elements(By.CSS_SELECTOR, "li[role='option'] span.multiselectcustom__option")
                if options:
                    break
            except:
                time.sleep(1)
        
        print(f"Found {len(options)} dropdown options")
        # Select last option regardless of text/visibility
        if options:
            driver.execute_script("arguments[0].click();", options[-1])
            print("Selected last dropdown option")
            time.sleep(2)
        
        # Click Download CSV button
        try:
            csv_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[normalize-space(text())='Download csv']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", csv_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", csv_button)
            try:
                csv_button.click()
            except:
                pass
            print("Clicked Download CSV button")
        except:
            print("Could not find download button")
        
        downloaded_file = wait_for_download(DOWNLOAD_DIR, DEFAULT_DOWNLOADS)
        if downloaded_file:
            filename = os.path.basename(downloaded_file)
            print(f"CSV downloaded: {filename}")
            log_download(url, filename)  # save to CSV
            return True
        else:
            print("Download failed or timed out")
            return False
            
    except Exception as e:
        print(f"Error processing screener: {e}")
        return False

def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"Reading links from: {LINKS_FILE}")
    links = read_links_from_file(LINKS_FILE)
    
    if not links:
        print("No valid links found. Exiting.")
        return
    
    print(f"Found {len(links)} valid links to process")
    
    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    wait = WebDriverWait(driver, WAIT_TIME)
    
    successful_downloads = 0
    failed_downloads = 0
    
    try:
        for i, url in enumerate(links, 1):
            success = process_screener(driver, wait, url, i, len(links))
            if success:
                successful_downloads += 1
            else:
                failed_downloads += 1
            
            if i < len(links):
                print("Waiting 2 seconds before next screener...")
                time.sleep(0)
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"Successful downloads: {successful_downloads}")
        print(f"Failed downloads: {failed_downloads}")
        print(f"Files saved to: {DOWNLOAD_DIR}")
        
    finally:
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    main()
