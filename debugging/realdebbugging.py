import pandas as pd

# Load the CSV file
df = pd.read_csv("your_file.csv")

# Assume column 2 has filenames and column 1 (index 0) has URLs
filename_col = df.iloc[:, 1]  # column with filenames
url_col = df.iloc[:, 0]       # column with URLs

# Find filenames that repeat
repeating_filenames = filename_col[filename_col.duplicated(keep=False)]

# Filter rows where filename repeats
rows_with_repeats = df[filename_col.isin(repeating_filenames)]

# Get only the URLs from those rows
urls = rows_with_repeats.iloc[:, 0].drop_duplicates()

# Print URLs
for url in urls:
    print(url)

# Save URLs to CSV
urls.to_csv("urls_with_repeating_filenames.csv", index=False, header=False)
