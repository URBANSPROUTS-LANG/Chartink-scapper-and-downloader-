import pandas as pd

file_path = r"C:\Users\Muthulk\Downloads\chartink_downloads - Copy.csv"

# Read CSV safely (force 3 columns, skip bad rows)
df = pd.read_csv(
    file_path,
    names=["url", "filename", "suffix"],
    header=None,
    on_bad_lines="skip",
    engine="python"
)

# Remove possible duplicate header row
df = df[df["url"] != "url"]

# Find duplicate filenames
duplicate_filenames = df[df.duplicated("filename", keep=False)]

# Keep only the URLs
duplicate_urls = duplicate_filenames[["url"]]

# Show results
print("URLs with duplicate filenames:")
print(duplicate_urls)

# Save to CSV
output_path = r"C:\Users\Muthulk\Downloads\duplicate_urls.csv"
duplicate_urls.to_csv(output_path, index=False)

print(f"\nResults saved to: {output_path}")
