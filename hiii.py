from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# ==== CONFIGURE CHROMEDRIVER ====
chromedriver_path = "C:/Users/Muthulk/Downloads/chromedriver.exe"  # <- Update this path
service = Service(chromedriver_path)

chrome_options = Options()
chrome_options.add_argument("--start-maximized")  # optional

driver = webdriver.Chrome(service=service, options=chrome_options)

# ==== OPEN THE PAGE ====
url = "https://chartink.com/screener/copy-breakout-weekly-trades-333"  # Change to your target page
driver.get(url)

# ==== WAIT FOR FILTERS TO LOAD ====
try:
    filters = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.atlas-filter-grabbable"))
    )
except:
    print("❌ Filters did not load.")
    driver.quit()
    exit()

# ==== CHECK FOR DAILY/WEEKLY/MONTHLY FILTERS ====
found = False

for f in filters:
    try:
        # Get the filter text (Daily / Weekly / Monthly)
        span_texts = [span.text.strip().lower() for span in f.find_elements(By.CSS_SELECTOR, ".atlas-offset")]
        filter_type = ", ".join(span_texts)

        # Check if filter is enabled (presence of Disable filter SVG)
        try:
            f.find_element(By.XPATH, ".//svg[@title='Disable filter']")
            enabled = True
        except NoSuchElementException:
            enabled = False

        if any(x in filter_type for x in ["daily", "weekly", "monthly"]) and enabled:
            print(f"✅ Matching filter found: {filter_type}, Enabled={enabled}")
            found = True
        else:
            print(f"❌ Not matching: {filter_type}, Enabled={enabled}")

    except Exception as e:
        print("⚠ Error reading a filter:", e)

if not found:
    print("❌ No enabled monthly/weekly/daily filter found.")

# ==== CLOSE DRIVER ====
driver.quit()
