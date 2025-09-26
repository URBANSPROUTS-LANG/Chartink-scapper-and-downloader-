import csv
import os

# Paths
downloads_folder = r'C:\Users\Muthulk\Downloads'
txt_file = os.path.join(downloads_folder, 'links.txt')
csv_file = os.path.join(downloads_folder, 'data.csv')

# Loop until txt file is empty
while True:
    # Read links from txt
    with open(txt_file, 'r', encoding='utf-8') as f:
        links = [line.strip() for line in f if line.strip()]

    if not links:
        print("All links processed and deleted from CSV.")
        break

    # Take the first link
    link_to_delete = links[0]
    print(f"Processing link: {link_to_delete}")

    # Read CSV and filter out rows containing the link
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = [row for row in reader if link_to_delete not in row]

    # Write back filtered CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    # Remove the processed link from txt
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.writelines("\n".join(links[1:]) + ("\n" if len(links) > 1 else ""))

    print(f"Deleted rows with link: {link_to_delete}")
