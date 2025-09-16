import os
import time
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
import re

# Configuration
LINKS_FILE = r"C:\Users\lavanya\Downloads\chartink_links.txt"
DOWNLOAD_DIR = r"C:\Users\lavanya\Downloads\Thrive_Data\toploved"
DEFAULT_DOWNLOADS = r"C:\Users\lavanya\Downloads\Thrive_Data\toploved"  # Default Chrome downloads folder
WAIT_TIME = 13  # Reduced from 30
DOWNLOAD_TIMEOUT = 20  # Reduced from 60

# Chrome options
chrome_options = Options()
chrome_options.debugger_address ="127.0.0.1:9233"
prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

def read_links_from_file(filename):
    """Read links from text file, one per line"""
    links = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
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
    """Wait for CSV file to be downloaded in either directory"""
    print(f"Monitoring directories:")
    print(f"   Primary: {primary_dir}")
    print(f"   Fallback: {fallback_dir}")
    
    end_time = time.time() + timeout
    
    # Get initial files from both directories
    def get_csv_files(directory):
        try:
            return glob.glob(os.path.join(directory, "*.csv"))
        except:
            return []
    
    initial_primary = get_csv_files(primary_dir)
    initial_fallback = get_csv_files(fallback_dir)
    initial_primary_count = len(initial_primary)
    initial_fallback_count = len(initial_fallback)
    
    print(f"Initial CSV files - Primary: {initial_primary_count}, Fallback: {initial_fallback_count}")
    
    while time.time() < end_time:
        # Check primary directory
        current_primary = get_csv_files(primary_dir)
        if len(current_primary) > initial_primary_count:
            latest_file = max(current_primary, key=os.path.getctime)
            print(f" New file in primary directory: {os.path.basename(latest_file)}")
            return latest_file
        
        # Check fallback directory (default Downloads)
        current_fallback = get_csv_files(fallback_dir)
        if len(current_fallback) > initial_fallback_count:
            latest_file = max(current_fallback, key=os.path.getctime)
            file_age = time.time() - os.path.getctime(latest_file)
            if file_age < 30:  # File created in last 30 seconds
                print(f"New file in fallback directory: {os.path.basename(latest_file)}")
                # Move file to primary directory
                try:
                    new_path = os.path.join(primary_dir, os.path.basename(latest_file))
                    os.rename(latest_file, new_path)
                    print(f"Moved to primary directory")
                    return new_path
                except Exception as e:
                    print(f" Could not move file: {e}")
                    return latest_file
        
        # Check for partial downloads
        crdownload_files = glob.glob(os.path.join(fallback_dir, "*.crdownload"))
        if crdownload_files:
            print(" Download in progress...")
        
        time.sleep(0.5)  # Check more frequently
    
    print("=Download timeout reached")
    return None

def sanitize_filename(url):
    """Create a safe filename from URL"""
    # Extract screener name from URL
    path = urlparse(url).path
    screener_name = path.split('/')[-1] if path.split('/')[-1] else 'screener'
    # Remove special characters
    safe_name = re.sub(r'[^\w\-_]', '_', screener_name)
    return safe_name

def process_screener(driver, wait, url, screener_num, total_screeners):
    """Process a single screener URL"""
    print(f"\n{'='*60}")
    print(f"Processing screener {screener_num}/{total_screeners}")
    print(f" URL: {url}")
    
    try:
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.ID, "backtest-container")))
        print("Backtest section loaded")
        
        # === Step 1: Find the dropdown container in backtest only ===
        backtest = driver.find_element(By.ID, "backtest-container")
        dropdown_container = backtest.find_element(By.CSS_SELECTOR, "div.custom-dropdown")
        driver.execute_script("arguments[0].click();", dropdown_container)
        print("Dropdown clicked (scoped inside backtest-container)")
        time.sleep(1)  # let it expand
        
        # === Step 2: Get options ONLY inside this dropdown (wait for them to load) ===
        print("Waiting for dropdown options to load...")
        time.sleep(2)  # Give time for options to load
        
        # Try multiple times to get options with text
        options = []
        for attempt in range(3):
            try:
                ul = dropdown_container.find_element(By.CSS_SELECTOR, "ul.multiselectcustom__content")
                options = ul.find_elements(By.CSS_SELECTOR, "li[role='option'] span.multiselectcustom__option")
                
                # Check if options have text
                options_with_text = [opt for opt in options if opt.text.strip()]
                if options_with_text:
                    options = options_with_text
                    break
                else:
                    print(f"Attempt {attempt + 1}: Options still loading...")
                    time.sleep(1)
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(1)
        
        print(f"Found {len(options)} dropdown options:")
        for i, opt in enumerate(options, 1):
            text = opt.text.strip()
            print(f"{i:02d}. '{text}' (displayed={opt.is_displayed()})")
        
        # === Step 3: Select the last option (longest timeframe) ===
        if options:
            selected_option = options[-1]
            driver.execute_script("arguments[0].click();", selected_option)
            selected_text = selected_option.text.strip()
            print(f"Selected: '{selected_text}'")
            time.sleep(2)  # Reduced wait time
        else:
            print("No options found in dropdown")
            return False
        
        # === Step 4: Download CSV ===
        try:
            csv_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[normalize-space(text())='Download csv']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", csv_button)
            time.sleep(2)
            
            print("Clicking Download CSV button...")
            driver.execute_script("arguments[0].click();", csv_button)
            
            # Alternative click methods if first one fails
            try:
                # Try regular click as backup
                csv_button.click()
            except:
                pass
            
            print("Waiting for download to start...")
            
        except Exception as e:
            print(f"Error clicking download button: {e}")
            # Try alternative selector
            try:
                alt_button = driver.find_element(By.XPATH, "//div[contains(text(), 'Download csv')]")
                driver.execute_script("arguments[0].click();", alt_button)
                print("Clicked alternative download button")
            except:
                print("Could not find download button")
                return False
        
        downloaded_file = wait_for_download(DOWNLOAD_DIR, DEFAULT_DOWNLOADS)
        if downloaded_file:
            # Rename file to include screener name
            screener_name = sanitize_filename(url)
            file_dir = os.path.dirname(downloaded_file)
            file_ext = os.path.splitext(downloaded_file)[1]
            new_filename = f"{screener_name}_{int(time.time())}{file_ext}"
            new_filepath = os.path.join(file_dir, new_filename)
            
            try:
                os.rename(downloaded_file, new_filepath)
                print(f"CSV downloaded and renamed: {new_filename}")
            except OSError as e:
                print(f"CSV downloaded: {os.path.basename(downloaded_file)} (rename failed: {e})")
            
            return True
        else:
            print(" Download failed or timed out")
            return False
            
    except Exception as e:
        print(f" Error processing screener: {str(e)}")
        return False

def main():
    """Main execution function"""
    # Create download directory if it doesn't exist
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Read links from file
    print(f" Reading links from: {LINKS_FILE}")
    links = read_links_from_file(LINKS_FILE)
    
    if not links:
        print("No valid links found. Exiting.")
        return
    
    print(f"Found {len(links)} valid links to process")
    
    # Initialize WebDriver
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
            
            # Small delay between requests to be respectful to the server
            if i < len(links):
                print("Waiting 2 seconds before next screener...")
                time.sleep(2)  # Reduced from 5 seconds
        
        # Summary
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"Successful downloads: {successful_downloads}")
        print(f"Failed downloads: {failed_downloads}")
        print(f" Files saved to: {DOWNLOAD_DIR}")
        
    finally:
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    main()
