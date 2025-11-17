"""Check Mercer Job Library Excel file contents."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pandas as pd

# Read Job Library Excel
excel_path = Path(__file__).parent / 'data' / 'Mercer' / 'Mercer Job Library.xlsx'
print(f"Reading: {excel_path}")
print()

df = pd.read_excel(excel_path)
print(f"Total rows in Excel: {len(df)}")
print(f"Columns: {list(df.columns)}")
print()

# Check for unique job codes
if 'MjlCode' in df.columns:
    unique_codes = df['MjlCode'].nunique()
    print(f"Unique job codes: {unique_codes}")
    print()

    # Sample first 5 rows
    print("First 5 rows:")
    print(df.head())
elif 'job_code' in df.columns:
    unique_codes = df['job_code'].nunique()
    print(f"Unique job codes: {unique_codes}")
    print()

    print("First 5 rows:")
    print(df.head())
else:
    print("Column names:")
    for col in df.columns:
        print(f"  - {col}")
    print()
    print("First row sample:")
    print(df.iloc[0])
