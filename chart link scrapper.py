import time
import re
import requests
from bs4 import BeautifulSoup

def selenium_extract_all_screeners():
    """
    Enhanced Selenium scraper to find ALL 13 screeners per page
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        print("🚀 ENHANCED SCREENER EXTRACTOR")
        print("=" * 50)
        print("Looking for ALL 13 screeners per page...")
        
        # Setup Chrome
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        all_screener_links = set()
        screener_details = []
        base_url = "https://chartink.com/screeners/top-loved-screeners"
        
        for page_num in range(1, 101):
            try:
                url = base_url if page_num == 1 else f"{base_url}?page={page_num}"
                print(f"\n📄 Page {page_num}: {url}")
                
                driver.get(url)
                time.sleep(4)  # Wait longer for content to load
                
                # Try multiple extraction strategies
                page_screeners = set()
                
                # Strategy 1: Get page source and use regex
                page_source = driver.page_source
                
                # Look for all screener URLs in the HTML using multiple patterns
                patterns = [
                    r'href=["\']([^"\']*\/screener\/[^"\']*)["\']',
                    r'"url":\s*"([^"]*\/screener\/[^"]*)"',
                    r'chartink\.com\/screener\/([a-zA-Z0-9\-_]+)',
                    r'\/screener\/([a-zA-Z0-9\-_]+)',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    for match in matches:
                        # Clean up the URL
                        if match.startswith('http'):
                            clean_url = match
                        elif match.startswith('/screener/'):
                            clean_url = f"https://chartink.com{match}"
                        elif '/screener/' in match:
                            clean_url = match if match.startswith('http') else f"https://chartink.com/{match.lstrip('/')}"
                        else:
                            # This is just the screener name/ID
                            clean_url = f"https://chartink.com/screener/{match}"
                        
                        # Remove query parameters and fragments
                        clean_url = clean_url.split('?')[0].split('#')[0]
                        page_screeners.add(clean_url)
                
                # Strategy 2: Look for specific div/container patterns
                try:
                    # Look for containers that might hold screener items
                    container_selectors = [
                        'div[class*="screener"]',
                        'div[class*="list"]',
                        'div[class*="item"]',
                        'div[class*="card"]',
                        '.py-2\\.5', # The class we saw in your example
                        '[class*="flex"]',
                    ]
                    
                    for selector in container_selectors:
                        try:
                            containers = driver.find_elements(By.CSS_SELECTOR, selector)
                            for container in containers:
                                # Look for links within each container
                                links_in_container = container.find_elements(By.TAG_NAME, "a")
                                for link in links_in_container:
                                    href = link.get_attribute("href")
                                    if href and '/screener/' in href:
                                        page_screeners.add(href)
                        except:
                            continue
                            
                except Exception as e:
                    print(f"  ⚠️ Error in strategy 2: {e}")
                
                # Strategy 3: Get ALL links and filter
                try:
                    all_links = driver.find_elements(By.TAG_NAME, "a")
                    for link in all_links:
                        try:
                            href = link.get_attribute("href")
                            if href and '/screener/' in href and 'chartink.com' in href:
                                page_screeners.add(href)
                        except:
                            continue
                except Exception as e:
                    print(f"  ⚠️ Error in strategy 3: {e}")
                
                # Strategy 4: Look in JavaScript variables
                try:
                    # Execute JavaScript to find any screener data
                    js_screeners = driver.execute_script("""
                        var screeners = [];
                        var allElements = document.getElementsByTagName('*');
                        for (var i = 0; i < allElements.length; i++) {
                            var elem = allElements[i];
                            var html = elem.innerHTML || '';
                            if (html.includes('/screener/')) {
                                var matches = html.match(/\/screener\/[a-zA-Z0-9\\-_]+/g);
                                if (matches) {
                                    for (var j = 0; j < matches.length; j++) {
                                        screeners.push('https://chartink.com' + matches[j]);
                                    }
                                }
                            }
                        }
                        return [...new Set(screeners)]; // Remove duplicates
                    """)
                    
                    for js_screener in js_screeners:
                        page_screeners.add(js_screener)
                        
                except Exception as e:
                    print(f"  ⚠️ Error in strategy 4: {e}")
                
                # Process all found screeners for this page
                new_screeners = []
                for screener_url in page_screeners:
                    if screener_url not in all_screener_links:
                        all_screener_links.add(screener_url)
                        
                        # Extract title from URL or try to get from page
                        screener_name = screener_url.split('/screener/')[-1].replace('-', ' ').title()
                        
                        screener_details.append({
                            'url': screener_url,
                            'title': screener_name,
                            'page': page_num
                        })
                        new_screeners.append(screener_url)
                
                print(f"  ✅ Found {len(new_screeners)} new screener links (Total strategies found: {len(page_screeners)})")
                
                # Show samples
                if new_screeners:
                    print(f"  📋 New screeners from page {page_num}:")
                    for i, url in enumerate(new_screeners[:5], 1):
                        screener_name = url.split('/screener/')[-1].replace('-', ' ').title()
                        print(f"    {i:2d}. {screener_name}")
                        print(f"        {url}")
                    
                    if len(new_screeners) > 5:
                        print(f"    ... and {len(new_screeners) - 5} more from this page")
                
                # If we're not finding around 13 per page after the first few pages, there might be an issue
                if page_num <= 10 and len(new_screeners) < 5:
                    print(f"  ⚠️ Warning: Only found {len(new_screeners)} screeners on page {page_num}")
                    print(f"      Expected around 13 per page. May need to adjust extraction logic.")
                
                # Check for pagination/next page
                if len(new_screeners) == 0 and page_num > 10:
                    consecutive_empty = getattr(selenium_extract_all_screeners, 'consecutive_empty', 0) + 1
                    selenium_extract_all_screeners.consecutive_empty = consecutive_empty
                    
                    if consecutive_empty >= 5:
                        print(f"  🛑 Stopping: {consecutive_empty} consecutive pages with no new results")
                        break
                else:
                    selenium_extract_all_screeners.consecutive_empty = 0
                
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ Error on page {page_num}: {e}")
                continue
        
        driver.quit()
        
        # Save results
        output_file = 'chartink_links.txt'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Chartink Screener Links - Enhanced Extraction\n")
            f.write(f"Scraped: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total unique screener links: {len(all_screener_links)}\n")
            f.write(f"Pages scraped: 1 to {page_num}\n")
            f.write("=" * 70 + "\n\n")
            
            # Detailed results grouped by page
            f.write("RESULTS BY PAGE:\n")
            f.write("-" * 40 + "\n")
            
            current_page = 0
            for detail in sorted(screener_details, key=lambda x: (x['page'], x['title'])):
                if detail['page'] != current_page:
                    current_page = detail['page']
                    f.write(f"\nPAGE {current_page}:\n")
                
                f.write(f"  • {detail['title']}\n")
                f.write(f"    {detail['url']}\n")
            
            # URLs only section
            f.write(f"\n{'=' * 70}\n")
            f.write("ALL URLS (for easy copying):\n")
            f.write(f"{'=' * 70}\n")
            
            for i, url in enumerate(sorted(all_screener_links), 1):
                f.write(f"{i:3d}. {url}\n")
        
        print(f"\n🎉 EXTRACTION COMPLETED!")
        print(f"📊 Total unique screener links found: {len(all_screener_links)}")
        print(f"💾 Results saved to: {output_file}")
        
        # Calculate statistics
        if screener_details:
            pages_with_results = len(set(d['page'] for d in screener_details))
            avg_per_page = len(all_screener_links) / pages_with_results if pages_with_results > 0 else 0
            print(f"📈 Statistics:")
            print(f"    - Pages with results: {pages_with_results}")
            print(f"    - Average per page: {avg_per_page:.1f}")
            print(f"    - Expected total (13/page × 100 pages): ~1300")
            print(f"    - Actual found: {len(all_screener_links)}")
        
        return list(all_screener_links)
        
    except ImportError:
        print("❌ Selenium not installed! Run: pip install selenium")
        return []
    except Exception as e:
        print(f"❌ Enhanced scraper failed: {e}")
        return []

if __name__ == "__main__":
    print("🎯 CHARTINK ENHANCED SCREENER EXTRACTOR")
    print("=" * 50)
    print("Target: Find ALL 13 screener links per page (13 × 100 = ~1300 total)")
    print("Using multiple extraction strategies...")
    
    links = selenium_extract_all_screeners()
    
    if links:
        print(f"\n✅ SUCCESS!")
        print(f"📊 Extracted {len(links)} total screener links")
        
        if len(links) < 500:
            print(f"\n⚠️ NOTICE: Found fewer links than expected")
            print(f"   Expected: ~1300 (13 per page × 100 pages)")
            print(f"   Found: {len(links)}")
            print(f"   This might indicate:")
            print(f"   - Some pages have fewer than 13 screeners")
            print(f"   - Website structure is different than expected")
            print(f"   - Some extraction strategies need refinement")
        
        print(f"\n📂 All results saved to: chartink_links.txt")
        
        # Show sample
        print(f"\n📋 SAMPLE RESULTS (first 10):")
        for i, link in enumerate(links[:10], 1):
            screener_name = link.split('/screener/')[-1].replace('-', ' ').title()
            print(f"{i:2d}. {screener_name}")
            print(f"    {link}")
        
        if len(links) > 10:
            print(f"    ... and {len(links) - 10} more links in the file")
            
    else:
        print(f"\n❌ No screener links found")
        print(f"Check that:")
        print(f"- Selenium and ChromeDriver are properly installed")
        print(f"- Internet connection is working")
        print(f"- Chartink website is accessible")
