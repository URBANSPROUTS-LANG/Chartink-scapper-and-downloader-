import os
import time
import glob
import csv
import shutil
from datetime import datetime, timedelta
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# === Configuration ===
CONFIG = {
    # File paths
    'LINKS_FILE': r'C:\Users\Muthulk\Downloads\y.txt',  # File containing screener URLs (one per line)
    'DOWNLOAD_DIR': r'C:\Users\Muthulk\Downloads',
    'OUTPUT_DIR': r'C:\Users\Muthulk\Downloads\processed_stocks',
    
    # Timing settings
    'RUN_INTERVAL_MINUTES': 1,     # For frequent runs (1 minute for testing)
    'DAILY_TIME': '18:00',         # Daily run time (6 PM in 24-hour format)
    'WAIT_TIME': 30,               # Selenium wait timeout
    'DOWNLOAD_TIMEOUT': 60,        # File download timeout
    'PAGE_LOAD_DELAY': 2,          # Delay after page load
    'AUTO_MODE': False,            # Set to True for automatic mode
    
    # CSV processing settings
    'COLUMNS_TO_EXTRACT': ['date', 'symbol', 'marketcapname', 'sector'],  # All columns from source
    'FILTER_TODAY_ONLY': True,  # Only extract today's stocks
    'PRESERVE_ORIGINAL_FILENAME': True,  # Keep original CSV filename
    'OUTPUT_FILENAME_PREFIX': 'stocks_data',  # Prefix for output files
    
    # Browser settings
    'HEADLESS': False,  # Set to True to run browser in background
    'CHROME_BINARY_PATH': None,  # Path to Chrome binary (None for auto-detect)
}

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'C:\Users\Muthulk\Downloads\stock_screener.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StockScreenerBot:
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.wait = None
        
        # Ensure directories exist
        os.makedirs(self.config['DOWNLOAD_DIR'], exist_ok=True)
        os.makedirs(self.config['OUTPUT_DIR'], exist_ok=True)
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with configured options."""
        chrome_options = Options()
        
        # Download preferences
        prefs = {
            "download.default_directory": self.config['DOWNLOAD_DIR'],
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Optional settings
        if self.config['HEADLESS']:
            chrome_options.add_argument("--headless")
        
        if self.config['CHROME_BINARY_PATH']:
            chrome_options.binary_location = self.config['CHROME_BINARY_PATH']
        
        # Additional Chrome options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        try:
            self.driver = webdriver.Chrome(service=Service(), options=chrome_options)
            self.wait = WebDriverWait(self.driver, self.config['WAIT_TIME'])
            logger.info("CHROME: WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"ERROR: Failed to initialize WebDriver: {e}")
            raise
    
    def get_today_date_ist(self):
        """Get today's date in IST timezone in various formats."""
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist)
        
        # Return multiple possible date formats that might appear in CSV
        # Note: Windows doesn't support %-m, so we'll handle single digit months differently
        formats = [
            today.strftime('%d-%m-%Y'),      # 23-09-2025
            today.strftime('%d/%m/%Y'),      # 23/09/2025  
            today.strftime('%m/%d/%Y'),      # 9/23/2025
            today.strftime('%Y-%m-%d'),      # 2025-09-23
        ]
        
        # Add single digit month formats manually
        if today.month < 10:
            formats.extend([
                f"{today.day}-{today.month}-{today.year}",     # 23-9-2025
                f"{today.day}/{today.month}/{today.year}",     # 23/9/2025
            ])
            
        return formats
    
    def is_today_date(self, date_str):
        """Check if the given date string matches today's date."""
        if not date_str or date_str.strip() == '':
            return False
            
        today_formats = self.get_today_date_ist()
        date_str = date_str.strip()
        
        # Direct match with today's formats
        if date_str in today_formats:
            return True
            
        # Try parsing different date formats (Windows-compatible)
        date_formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d',
            '%d-%m-%y', '%d/%m/%y', '%m/%d/%y', '%y-%m-%d'
        ]
        
        today_date = datetime.now(pytz.timezone('Asia/Kolkata')).date()
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                if parsed_date == today_date:
                    return True
            except ValueError:
                continue
        
        # Try manual parsing for single digit months/days
        try:
            parts = date_str.replace('/', '-').split('-')
            if len(parts) == 3:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                if year < 100:  # Handle 2-digit years
                    year += 2000
                parsed_date = datetime(year, month, day).date()
                if parsed_date == today_date:
                    return True
        except (ValueError, IndexError):
            pass
                
        return False
    
    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("BROWSER: Browser closed")
    
    def load_links(self):
        """Load screener URLs from file."""
        try:
            with open(self.config['LINKS_FILE'], 'r', encoding='utf-8') as file:
                links = [line.strip() for line in file if line.strip() and not line.startswith('#')]
            logger.info(f"LINKS: Loaded {len(links)} links from {self.config['LINKS_FILE']}")
            return links
        except FileNotFoundError:
            logger.error(f"ERROR: Links file '{self.config['LINKS_FILE']}' not found")
            return []
        except Exception as e:
            logger.error(f"ERROR: Error loading links: {e}")
            return []
    
    def wait_for_download(self, timeout=None):
        """Wait until a CSV file appears in download directory."""
        if timeout is None:
            timeout = self.config['DOWNLOAD_TIMEOUT']
        
        # Get existing CSV files before download
        existing_files = set(glob.glob(os.path.join(self.config['DOWNLOAD_DIR'], "*.csv")))
        
        end_time = time.time() + timeout
        while time.time() < end_time:
            current_files = set(glob.glob(os.path.join(self.config['DOWNLOAD_DIR'], "*.csv")))
            new_files = current_files - existing_files
            
            if new_files:
                # Return the most recently created new file
                newest_file = max(new_files, key=os.path.getctime)
                
                # Wait a bit more to ensure download is complete
                time.sleep(2)
                if os.path.exists(newest_file) and os.path.getsize(newest_file) > 0:
                    return newest_file
            
            time.sleep(1)
        
        return None
    
    def download_csv_from_url(self, url):
        """Download CSV from a single screener URL."""
        try:
            logger.info(f"SCRAPER: Opening screener: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(self.config['PAGE_LOAD_DELAY'])
            
            # Wait for backtest container to load
            self.wait.until(EC.presence_of_element_located((By.ID, "backtest-container")))
            logger.info("SUCCESS: Backtest section loaded")
            
            # Find and click Download CSV button
            csv_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[normalize-space(text())='Download csv']"))
            )
            
            # Scroll to button and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", csv_button)
            time.sleep(1)
            csv_button.click()
            logger.info("DOWNLOAD: Clicked Download CSV... waiting for file")
            
            # Wait for download to complete
            downloaded_file = self.wait_for_download()
            
            if downloaded_file:
                logger.info(f"SUCCESS: CSV downloaded: {os.path.basename(downloaded_file)}")
                return downloaded_file
            else:
                logger.error("ERROR: Download failed or timed out")
                return None
                
        except TimeoutException:
            logger.error(f"ERROR: Timeout while processing {url}")
            return None
        except NoSuchElementException:
            logger.error(f"ERROR: Download button not found for {url}")
            return None
        except Exception as e:
            logger.error(f"ERROR: Error downloading from {url}: {e}")
            return None
    
    def process_csv(self, csv_file, url_index):
        """Process downloaded CSV and extract only today's stocks."""
        try:
            # Get original filename without extension
            original_filename = os.path.splitext(os.path.basename(csv_file))[0]
            
            if self.config['PRESERVE_ORIGINAL_FILENAME']:
                output_filename = f"{original_filename}_today.csv"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{self.config['OUTPUT_FILENAME_PREFIX']}_{url_index+1}_{timestamp}.csv"
            
            output_path = os.path.join(self.config['OUTPUT_DIR'], output_filename)
            
            with open(csv_file, 'r', encoding='utf-8') as infile:
                # Try different delimiters
                sample = infile.read(1024)
                infile.seek(0)
                
                delimiter = '\t' if '\t' in sample else ','
                reader = csv.DictReader(infile, delimiter=delimiter)
                
                # Check available columns
                available_columns = reader.fieldnames
                logger.info(f"CSV: Available columns in file: {available_columns}")
                
                # Verify required columns exist
                required_columns = self.config['COLUMNS_TO_EXTRACT']
                missing_columns = [col for col in required_columns if col not in available_columns]
                
                if missing_columns:
                    logger.error(f"ERROR: Missing columns {missing_columns} in {csv_file}")
                    return None
                
                # Write processed CSV with today's stocks only
                today_stocks = []
                total_rows = 0
                
                for row in reader:
                    total_rows += 1
                    if self.config['FILTER_TODAY_ONLY']:
                        # Check if this row is for today
                        date_value = row.get('date', '')
                        if self.is_today_date(date_value):
                            today_stocks.append(row)
                    else:
                        today_stocks.append(row)
                
                # Write the filtered results (append mode)
                file_exists = os.path.exists(output_path)
                
                with open(output_path, 'a', newline='', encoding='utf-8') as outfile:
                    writer = csv.DictWriter(outfile, fieldnames=required_columns)
                    
                    # Only write header if file doesn't exist
                    if not file_exists:
                        writer.writeheader()
                    
                    # Write today's stocks
                    for stock in today_stocks:
                        filtered_row = {col: stock.get(col, '') for col in required_columns}
                        writer.writerow(filtered_row)
                
                if len(today_stocks) == 0:
                    logger.warning("WARNING: No stocks found for today's date")
                    # Still create/touch the file even if no data, but don't write empty rows
                    if not file_exists:
                        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
                            writer = csv.DictWriter(outfile, fieldnames=required_columns)
                            writer.writeheader()
                else:
                    # Show sample of today's stocks
                    logger.info(f"TODAY'S STOCKS: {[stock['symbol'] for stock in today_stocks[:5]]}")
                    if len(today_stocks) > 5:
                        logger.info(f"... and {len(today_stocks) - 5} more stocks")
                
                action = "Appended to" if file_exists else "Created"
                logger.info(f"SUCCESS: {action} CSV file: {output_filename}")
                logger.info(f"STATS: Added {len(today_stocks)} today's stocks (out of {total_rows} total rows processed)")
                    
            # Delete original downloaded file
            os.remove(csv_file)
            logger.info(f"CLEANUP: Deleted original file: {os.path.basename(csv_file)}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"ERROR: Error processing CSV {csv_file}: {e}")
            return None
    
    def run_single_cycle(self):
        """Run one complete cycle of downloading and processing all URLs."""
        links = self.load_links()
        
        if not links:
            logger.error("ERROR: No links to process")
            return
        
        self.setup_driver()
        
        try:
            successful_downloads = 0
            
            for i, url in enumerate(links):
                logger.info(f"PROGRESS: Processing link {i+1}/{len(links)}: {url}")
                
                # Download CSV
                downloaded_file = self.download_csv_from_url(url)
                
                if downloaded_file:
                    # Process CSV
                    processed_file = self.process_csv(downloaded_file, i)
                    if processed_file:
                        successful_downloads += 1
                
                # Small delay between downloads
                if i < len(links) - 1:
                    time.sleep(2)
            
            logger.info(f"COMPLETE: Cycle completed: {successful_downloads}/{len(links)} files processed successfully")
            
        finally:
            self.close_driver()
    
    def run_every_minute(self):
        """Run the bot every minute continuously."""
        logger.info(f"SCHEDULER: Starting every-minute mode. Running every {self.config['RUN_INTERVAL_MINUTES']} minute(s)")
        
        while True:
            try:
                cycle_start = datetime.now()
                logger.info(f"CYCLE: Starting cycle at {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
                
                self.run_single_cycle()
                
                cycle_end = datetime.now()
                cycle_duration = (cycle_end - cycle_start).total_seconds() / 60
                logger.info(f"COMPLETE: Cycle completed in {cycle_duration:.1f} minutes")
                
                # Calculate next run time
                next_run = cycle_start + timedelta(minutes=self.config['RUN_INTERVAL_MINUTES'])
                logger.info(f"SCHEDULE: Next run at: {next_run.strftime('%H:%M:%S')}")
                
                # Sleep until next run
                sleep_minutes = self.config['RUN_INTERVAL_MINUTES'] - cycle_duration
                if sleep_minutes > 0:
                    logger.info(f"WAIT: Sleeping for {sleep_minutes:.1f} minutes...")
                    time.sleep(sleep_minutes * 60)
                else:
                    logger.warning("WARNING: Cycle took longer than interval! Starting next cycle immediately.")
                
            except KeyboardInterrupt:
                logger.info("STOP: Received interrupt signal. Stopping...")
                break
            except Exception as e:
                logger.error(f"ERROR: Error in every-minute mode: {e}")
                logger.info(f"RETRY: Retrying in 30 seconds...")
    def run_daily_schedule(self):
        """Run the bot on a daily schedule at 6 PM."""
        logger.info(f"SCHEDULER: Starting daily mode. Will run every day at {self.config['DAILY_TIME']}")
        
        while True:
            try:
                # Calculate next run time
                ist = pytz.timezone('Asia/Kolkata')
                now = datetime.now(ist)
                
                # Parse the scheduled time
                hour, minute = map(int, self.config['DAILY_TIME'].split(':'))
                
                # Get today's scheduled time
                today_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If today's time has passed, schedule for tomorrow
                if now >= today_run:
                    next_run = today_run + timedelta(days=1)
                else:
                    next_run = today_run
                
                # Calculate sleep time
                sleep_seconds = (next_run - now).total_seconds()
                
                logger.info(f"SCHEDULE: Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')} IST")
                logger.info(f"WAIT: Sleeping for {sleep_seconds/3600:.1f} hours...")
                
                # Sleep until next run
                time.sleep(sleep_seconds)
                
                # Run the cycle
                cycle_start = datetime.now(ist)
                logger.info(f"CYCLE: Starting daily cycle at {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
                
                self.run_single_cycle()
                
                cycle_end = datetime.now(ist)
                cycle_duration = (cycle_end - cycle_start).total_seconds() / 60
                logger.info(f"COMPLETE: Daily cycle completed in {cycle_duration:.1f} minutes")
                
            except KeyboardInterrupt:
                logger.info("STOP: Received interrupt signal. Stopping daily scheduler...")
                break
            except Exception as e:
                logger.error(f"ERROR: Error in daily scheduler: {e}")
                logger.info("RETRY: Retrying in 30 minutes...")
                time.sleep(1800)  # Wait 30 minutes before retry
        """Run the bot on a daily schedule at the specified time."""
        logger.info(f"SCHEDULER: Starting daily mode. Will run every day at {self.config['SCHEDULED_TIME']}")
        
        while True:
            try:
                # Calculate next run time
                ist = pytz.timezone('Asia/Kolkata')
                now = datetime.now(ist)
                
                # Parse the scheduled time
                hour, minute = map(int, self.config['SCHEDULED_TIME'].split(':'))
                
                # Get today's scheduled time
                today_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If today's time has passed, schedule for tomorrow
                if now >= today_run:
                    next_run = today_run + timedelta(days=1)
                else:
                    next_run = today_run
                
                # Calculate sleep time
                sleep_seconds = (next_run - now).total_seconds()
                
                logger.info(f"SCHEDULE: Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')} IST")
                logger.info(f"WAIT: Sleeping for {sleep_seconds/3600:.1f} hours...")
                
                # Sleep until next run
                time.sleep(sleep_seconds)
                
                # Run the cycle
                cycle_start = datetime.now(ist)
                logger.info(f"CYCLE: Starting daily cycle at {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
                
                self.run_single_cycle()
                
                cycle_end = datetime.now(ist)
                cycle_duration = (cycle_end - cycle_start).total_seconds() / 60
                logger.info(f"COMPLETE: Daily cycle completed in {cycle_duration:.1f} minutes")
                
            except KeyboardInterrupt:
                logger.info("STOP: Received interrupt signal. Stopping daily scheduler...")
                break
            except Exception as e:
                logger.error(f"ERROR: Error in daily scheduler: {e}")
                logger.info("RETRY: Retrying in 30 minutes...")
    def run_continuous(self):
        """Run the bot continuously with configured intervals."""
        logger.info(f"SCHEDULER: Starting continuous mode. Running every {self.config['RUN_INTERVAL_MINUTES']} minutes")
        
        while True:
            try:
                cycle_start = datetime.now()
                logger.info(f"CYCLE: Starting new cycle at {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
                
                self.run_single_cycle()
                
                cycle_end = datetime.now()
                cycle_duration = (cycle_end - cycle_start).total_seconds() / 60
                logger.info(f"COMPLETE: Cycle completed in {cycle_duration:.1f} minutes")
                
                # Calculate next run time
                next_run = cycle_start + timedelta(minutes=self.config['RUN_INTERVAL_MINUTES'])
                logger.info(f"SCHEDULE: Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Sleep until next run
                sleep_minutes = self.config['RUN_INTERVAL_MINUTES'] - cycle_duration
                if sleep_minutes > 0:
                    logger.info(f"WAIT: Sleeping for {sleep_minutes:.1f} minutes...")
                    time.sleep(sleep_minutes * 60)
                else:
                    logger.warning("WARNING: Cycle took longer than interval! Starting next cycle immediately.")
                
            except KeyboardInterrupt:
                logger.info("STOP: Received interrupt signal. Stopping...")
                break
            except Exception as e:
                logger.error(f"ERROR: Error in continuous mode: {e}")
                logger.info(f"RETRY: Retrying in 5 minutes...")
                time.sleep(300)  # Wait 5 minutes before retry
        """Run the bot continuously with configured intervals."""
        logger.info(f"SCHEDULER: Starting continuous mode. Running every {self.config['RUN_INTERVAL']} minutes")
        
        while True:
            try:
                cycle_start = datetime.now()
                logger.info(f"CYCLE: Starting new cycle at {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
                
                self.run_single_cycle()
                
                cycle_end = datetime.now()
                cycle_duration = (cycle_end - cycle_start).total_seconds() / 60
                logger.info(f"COMPLETE: Cycle completed in {cycle_duration:.1f} minutes")
                
                # Calculate next run time
                next_run = cycle_start + timedelta(minutes=self.config['RUN_INTERVAL'])
                logger.info(f"SCHEDULE: Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Sleep until next run
                sleep_minutes = self.config['RUN_INTERVAL'] - cycle_duration
                if sleep_minutes > 0:
                    logger.info(f"WAIT: Sleeping for {sleep_minutes:.1f} minutes...")
                    time.sleep(sleep_minutes * 60)
                else:
                    logger.warning("WARNING: Cycle took longer than interval! Starting next cycle immediately.")
                
            except KeyboardInterrupt:
                logger.info("STOP: Received interrupt signal. Stopping...")
                break
            except Exception as e:
                logger.error(f"ERROR: Error in continuous mode: {e}")
                logger.info(f"RETRY: Retrying in 5 minutes...")
                time.sleep(300)  # Wait 5 minutes before retry

def main():
    """Main function to run the stock screener bot."""
    print("STOCK SCREENER: Stock Screener Automation Bot")
    print("=" * 50)
    
    # Create bot instance
    bot = StockScreenerBot(CONFIG)
    
    # Check if auto mode is enabled
    if CONFIG['AUTO_MODE']:
        logger.info("AUTO: Auto mode enabled - running daily scheduler")
        bot.run_daily_schedule()
    else:
        # Ask user for run mode
        print("\nSelect run mode:")
        print("1. Run once")
        print("2. Run every 1 minute (for testing)")  
        print("3. Run daily at 6 PM")
        print("4. Custom continuous interval")
        
        choice = input("Enter choice (1, 2, 3, or 4): ").strip()
        
        if choice == "1":
            logger.info("MODE: Running in single-cycle mode")
            bot.run_single_cycle()
        elif choice == "2":
            logger.info("MODE: Running every 1 minute")
            bot.run_every_minute()
        elif choice == "3":
            logger.info("MODE: Running daily at 6 PM")
            bot.run_daily_schedule()
        elif choice == "4":
            try:
                interval = int(input("Enter interval in minutes: "))
                if interval > 0:
                    bot.config['RUN_INTERVAL_MINUTES'] = interval
                    logger.info(f"MODE: Running every {interval} minutes")
                    bot.run_continuous()
                else:
                    logger.error("ERROR: Interval must be greater than 0")
            except ValueError:
                logger.error("ERROR: Invalid interval. Please enter a number.")
        else:
            logger.error("ERROR: Invalid choice. Exiting.")
            return
    
    print("\nCOMPLETE: Bot execution completed!")

if __name__ == "__main__":
    main()
