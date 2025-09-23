import os
import shutil
import re
import difflib

# ==== CONFIG ====
downloads = r"C:\Users\Muthulk\Downloads"
links_file = os.path.join(downloads, "y.txt")  # text file with links
files_folder = os.path.join(downloads, "New folder (3)")  # folder with your files
output_matched = os.path.join(downloads, "matched")
output_unmatched = os.path.join(downloads, "unmatched")

# Create output folders if they don't exist
os.makedirs(output_matched, exist_ok=True)
os.makedirs(output_unmatched, exist_ok=True)

# --- Load links ---
with open(links_file, "r", encoding="utf-8") as f:
    raw_links = [line.strip() for line in f if line.strip()]

# --- Normalize function ---
def normalize(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9]+', '-', name)  # replace non-alphanumeric with dash
    name = name.strip('-')
    return name

# --- Extract normalized link IDs ---
link_ids = {}
for link in raw_links:
    screener = link.split("/")[-1]  # last part of URL
    link_ids[normalize(screener)] = link

# --- Match files with fuzzy logic ---
for file_name in os.listdir(files_folder):
    file_path = os.path.join(files_folder, file_name)

    if not os.path.isfile(file_path):
        continue

    base_name = os.path.splitext(file_name)[0]
    norm_name = normalize(base_name)

    # find the best fuzzy match among links
    best_match = difflib.get_close_matches(norm_name, link_ids.keys(), n=1, cutoff=0.5)

    if best_match:
        shutil.move(file_path, os.path.join(output_matched, file_name))
    else:
        shutil.move(file_path, os.path.join(output_unmatched, file_name))

print("✅ Done! Check your Downloads folder for 'matched' and 'unmatched'.")
