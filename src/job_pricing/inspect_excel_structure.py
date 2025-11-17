"""Inspect Mercer Job Library Excel structure."""
import pandas as pd
from pathlib import Path

excel_path = Path(__file__).parent / 'data' / 'Mercer' / 'Mercer Job Library.xlsx'

print(f"Reading: {excel_path}")
print()

# Try reading with different header rows
for header_row in [0, 1, 5, 10]:
    print(f"=== Trying header_row={header_row} ===")
    try:
        df = pd.read_excel(excel_path, sheet_name="Mercer Combined Jobs and Jobs", header=header_row)
        print(f"Rows: {len(df)}")
        print(f"Columns: {list(df.columns[:10])}")  # First 10 columns

        # Check for job code column
        possible_codes = [col for col in df.columns if 'code' in str(col).lower() or 'mjl' in str(col).lower()]
        if possible_codes:
            print(f"Possible job code columns: {possible_codes}")

        # Show first row
        print("First row sample:")
        print(df.iloc[0].head(5))
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
