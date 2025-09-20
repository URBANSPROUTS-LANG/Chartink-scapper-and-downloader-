from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import os

# ==== CONFIGURATION ====
chromedriver_path = "C:/Users/Muthulk/Downloads/chromedriver.exe"
input_file = "C:/Users/Muthulk/Downloads/t.txt"
output_file = "C:/Users/Muthulk/Downloads/no_weekly_monthly.txt"
log_file = "C:/Users/Muthulk/Downloads/processing_log.txt"

# Chrome options for faster processing
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in background
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-images")
chrome_options.add_argument("--disable-javascript")  # Might speed up loading
chrome_options.add_argument("--window-size=1024,768")

service = Service(chromedriver_path)

def check_daily_filter_enabled(driver, url, timeout=10):
    """
    Check if a URL has NO enabled weekly/monthly filters.
    Daily filters can be enabled or not available - doesn't matter.
    Returns: (meets_criteria, filter_info)
    """
    try:
        print(f"🌐 Checking: {url}")
        driver.get(url)
        time.sleep(2)  # Brief wait for page load
        
        # Wait for filters to load
        try:
            filters = WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.atlas-filter-grabbable"))
            )
        except TimeoutException:
            return False, "Filters did not load"
        
        daily_enabled = False
        weekly_enabled = False
        monthly_enabled = False
        filter_details = []
        
        for i, filter_element in enumerate(filters):
            try:
                # Get filter text
                span_texts = [span.text.strip().lower() for span in filter_element.find_elements(By.CSS_SELECTOR, ".atlas-offset")]
                filter_type = ", ".join(span_texts)
                
                # Check if filter is enabled
                enabled = False
                
                # Method 1: Check for "Disable filter" SVG
                try:
                    filter_element.find_element(By.XPATH, ".//svg[@title='Disable filter']")
                    enabled = True
                except NoSuchElementException:
                    pass
                
                # Method 2: SVG path analysis
                if not enabled:
                    try:
                        svg_paths = filter_element.find_elements(By.CSS_SELECTOR, "svg path")
                        for path in svg_paths:
                            path_data = path.get_attribute("d")
                            if path_data:
                                # Using the corrected logic
                                if ("9.5" in path_data and "10.5" in path_data) or ("10.5 4.5H5.5" in path_data):
                                    enabled = True
                                    break
                    except:
                        pass
                
                # Check filter type and status
                if "daily" in filter_type:
                    filter_details.append(f"Daily: {enabled}")
                    if enabled:
                        daily_enabled = True
                elif "weekly" in filter_type:
                    filter_details.append(f"Weekly: {enabled}")
                    if enabled:
                        weekly_enabled = True
                elif "monthly" in filter_type:
                    filter_details.append(f"Monthly: {enabled}")
                    if enabled:
                        monthly_enabled = True
                    
            except Exception as e:
                continue
        
        # CRITERIA: NO weekly enabled AND NO monthly enabled
        # (Daily doesn't matter - can be enabled or not available)
        meets_criteria = not weekly_enabled and not monthly_enabled
        
        if not filter_details:
            # If no daily/weekly/monthly filters found, it meets criteria
            return True, "No daily/weekly/monthly filters found - OK"
        
        status_summary = " | ".join(filter_details)
        if meets_criteria:
            status_summary += " | ✅ CRITERIA MET (No weekly/monthly enabled)"
        else:
            reasons = []
            if weekly_enabled:
                reasons.append("Weekly enabled")
            if monthly_enabled:
                reasons.append("Monthly enabled")
            status_summary += f" | ❌ REJECTED: {', '.join(reasons)}"
        
        return meets_criteria, status_summary
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    # Read URLs from file
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        all_urls = [line.strip() for line in f.readlines() if line.strip()]
    
    # PROCESS ALL URLs
    urls = all_urls
    
    print(f"📂 Found {len(urls)} URLs to process")
    
    # Initialize results
    daily_enabled_urls = []
    processed_count = 0
    
    # Start browser
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Open log file for writing
        with open(log_file, 'w', encoding='utf-8') as log:
            log.write("URL Processing Log\n")
            log.write("=" * 50 + "\n")
            
            for i, url in enumerate(urls, 1):
                try:
                    # Check the URL
                    has_daily_enabled, info = check_daily_filter_enabled(driver, url)
                    
                    # Log the result
                    status = "✅ ACCEPTED" if has_daily_enabled else "❌ REJECTED"
                    log_entry = f"{i:4d}/{len(urls)} | {status} | {url} | {info}\n"
                    log.write(log_entry)
                    log.flush()  # Ensure it's written immediately
                    
                    print(f"{i:4d}/{len(urls)} | {status} | {info}")
                    
                    # If criteria met, add to results
                    if has_daily_enabled:
                        daily_enabled_urls.append(url)
                        print(f"    🎯 Added to results! (Total found: {len(daily_enabled_urls)})")
                    
                    processed_count += 1
                    
                    # Save progress every 50 URLs
                    if processed_count % 50 == 0:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(daily_enabled_urls))
                        print(f"💾 Progress saved: {len(daily_enabled_urls)} qualifying URLs found so far")
                    
                    # Small delay to be respectful to the server
                    time.sleep(1)
                    
                except Exception as e:
                    error_msg = f"{i:4d}/{len(urls)} | ❌ ERROR | {url} | {str(e)}\n"
                    log.write(error_msg)
                    print(f"⚠ Error processing {url}: {e}")
                    continue
    
    finally:
        driver.quit()
    
    # Save final results
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(daily_enabled_urls))
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🎉 PROCESSING COMPLETE!")
    print(f"📊 Total URLs processed: {processed_count}")
    print(f"✅ URLs with NO weekly/monthly enabled: {len(daily_enabled_urls)}")
    print(f"💾 Results saved to: {output_file}")
    print(f"📋 Full log saved to: {log_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
