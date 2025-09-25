import pandas as pd

file_path = r"C:\Users\Muthulk\Downloads\chartink_downloads - Copy.csv"

# Read CSV while skipping problematic lines and forcing 3 columns
df = pd.read_csv(
    file_path,
    names=["url", "filename", "suffix"],  # force 3 columns
    header=None,  # ignore the first row as header
    on_bad_lines="skip",  # skip rows with too many/few columns
    engine="python"  # more tolerant parser
)

# Remove possible duplicate header row (since we forced names)
df = df[df["url"] != "url"]

# Group by filename and collect all URLs
duplicates = df.groupby("filename")["url"].apply(list).reset_index()

# Keep only filenames that appear more than once
duplicates = duplicates[duplicates["url"].str.len() > 1]

# Show results
print("Filenames with exact matches and their URLs:")
print(duplicates)

# Save results
output_path = r"C:\Users\Muthulk\Downloads\matching_filenames.csv"
duplicates.to_csv(output_path, index=False)

print(f"\nResults saved to: {output_path}")
