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

# Remove possible duplicate header row
df = df[df["url"] != "url"]

# Add a duplicate count per filename (1-based)
df['dup_count'] = df.groupby('filename').cumcount() + 1

# Keep all duplicates except the first
all_but_first_duplicates = df[df['dup_count'] > 1]

# Show results
print("Second, third, fourth, ... occurrences of duplicates:")
print(all_but_first_duplicates)

# Save results
output_path = r"C:\Users\Muthulk\Downloads\duplicates_except_first.csv"
all_but_first_duplicates.to_csv(output_path, index=False)

print(f"\nResults saved to: {output_path}")
