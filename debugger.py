import re
from collections import Counter

LOG_FILE = r"C:\Users\Muthulk\Downloads\chartink_log.txt"

def analyze_log(log_file):
    with open(log_file, "r", encoding="utf-8") as f:
        log_data = f.read()

    # Find all "CSV downloaded: filename" lines
    matches = re.findall(r"CSV downloaded:\s+(.+\.csv)", log_data)

    total_logged = len(matches)
    unique_files = set(matches)
    duplicates = [f for f, c in Counter(matches).items() if c > 1]

    print("="*60)
    print(f"Total 'successful downloads' in log: {total_logged}")
    print(f"Unique CSV filenames: {len(unique_files)}")
    print(f"Duplicate filenames reused: {len(duplicates)}")
    print("="*60)

    if duplicates:
        print("Examples of duplicates (logged multiple times):")
        for f in duplicates[:20]:  # show up to 20 duplicates
            print(f" - {f} (count {matches.count(f)})")

if __name__ == "__main__":
    analyze_log(LOG_FILE)
