import re
import csv
from collections import defaultdict

LOG_FILE = r"C:\Users\Muthulk\Downloads\chartink_log.txt"
OUT_FILE = r"C:\Users\Muthulk\Downloads\chartink_analysis.csv"

def analyze_log(log_file, out_file):
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    results = []
    current_url = None
    screener_num = None

    for line in lines:
        match_proc = re.search(r"Processing screener (\d+)/(\d+)", line)
        if match_proc:
            screener_num = int(match_proc.group(1))
            continue

        match_url = re.search(r"URL:\s+(https?://\S+)", line)
        if match_url:
            current_url = match_url.group(1)
            continue

        match_csv = re.search(r"CSV downloaded:\s+(.+\.csv)", line)
        if match_csv and current_url:
            filename = match_csv.group(1).strip()
            results.append((screener_num, current_url, filename))

    # Track duplicates
    seen = {}
    rows = []
    for num, url, fname in results:
        if fname in seen:
            first_seen = seen[fname]
            status = f"Duplicate (first at screener {first_seen})"
        else:
            seen[fname] = num
            status = "Unique"
        rows.append([num, url, fname, status])

    # Write CSV
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Screener #", "URL", "Filename", "Status"])
        writer.writerows(rows)

    print("="*80)
    print(f"Exported {len(rows)} screener entries")
    print(f"Unique filenames: {len(seen)}")
    print(f"Duplicates: {len(rows) - len(seen)}")
    print(f"Saved analysis to {out_file}")

if __name__ == "__main__":
    analyze_log(LOG_FILE, OUT_FILE)
