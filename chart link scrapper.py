#!/usr/bin/env python3
"""
scrape_chartink_selenium_txt.py
Scrapes Chartink "Top Loved Screeners" pages using Selenium (Chrome)
and saves all screener links into chartink_screeners.txt
"""

import argparse
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

BASE = "https://chartink.com"
LISTING_PATH = "/screeners/top-loved-screeners"

def make_driver(headless=True, use_wm=False):
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
    if use_wm:
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)
    else:
        driver = webdriver.Chrome(options=opts)
    return driver

def extract_links_from_driver(driver):
    anchors = driver.find_elements(By.TAG_NAME, "a")
    links = set()
    for a in anchors:
        href = a.get_attribute("href")
        if href and "/screener/" in href:
            links.add(href.split("?")[0])
    return links

def main(start, end, headless, use_wm, delay_min, delay_max):
    driver = None
    found = set()
    try:
        driver = make_driver(headless=headless, use_wm=use_wm)
    except WebDriverException as e:
        print("Error launching Chrome webdriver:", e)
        return

    try:
        for page in range(start, end + 1):
            url = f"{BASE}{LISTING_PATH}?page={page}"
            print(f"[{page}] Opening {url}")
            driver.get(url)
            time.sleep(2.0)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.0)
            links = extract_links_from_driver(driver)
            if links:
                print(f" found {len(links)} links")
                found.update(links)
            else:
                print(" no screener links found on page")
            time.sleep(random.uniform(delay_min, delay_max))
    finally:
        driver.quit()

    # Save as TXT
    with open("chartink_screeners.txt", "w", encoding="utf-8") as f:
        for u in sorted(found):
            f.write(u + "\n")

    print(f"\nDone. Unique screener links: {len(found)}")
    print("Saved to: chartink_screeners.txt")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--end", type=int, default=100)
    p.add_argument("--headless", action="store_true", help="Run Chrome headless")
    p.add_argument("--use-webdriver-manager", dest="use_wm", action="store_true",
                   help="Use webdriver-manager to auto-install chromedriver")
    p.add_argument("--delay-min", type=float, default=1.0)
    p.add_argument("--delay-max", type=float, default=2.0)
    args = p.parse_args()
    main(args.start, args.end, args.headless, args.use_wm, args.delay_min, args.delay_max)
