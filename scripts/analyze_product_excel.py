"""
Analyze Product Excel File Structure
Quick diagnostic to understand the data before loading
"""

import pandas as pd
import sys
from pathlib import Path

# File path
EXCEL_FILE = Path(__file__).parent.parent / "docs" / "reference" / "ProductData (Top 3 Cats).xlsx"

def main():
    print("="*80)
    print("HORME PRODUCT DATA ANALYSIS")
    print("="*80)
    print(f"\nFile: {EXCEL_FILE}")

    if not EXCEL_FILE.exists():
        print(f"ERROR: File not found!")
        sys.exit(1)

    print(f"File exists ({EXCEL_FILE.stat().st_size:,} bytes)")

    # Read Excel file
    print("\nReading Excel File...")
    excel_file = pd.ExcelFile(EXCEL_FILE)

    print(f"\nSheet Names: {excel_file.sheet_names}")

    # Analyze each sheet
    for sheet_name in excel_file.sheet_names:
        print("\n" + "="*80)
        print(f"SHEET: {sheet_name}")
        print("="*80)

        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)

        print(f"\nDimensions: {df.shape[0]} rows x {df.shape[1]} columns")
        print(f"\nColumns: {list(df.columns)}")

        print(f"\nSample Data (first 5 rows):")
        print(df.head())

        print(f"\nData Types:")
        print(df.dtypes)

        print(f"\nNull Values:")
        print(df.isnull().sum())

        # Category distribution
        if 'Category' in df.columns:
            print(f"\nCategory Distribution:")
            print(df['Category'].value_counts())

        # Brand distribution
        if 'Brand' in df.columns:
            print(f"\nTop 10 Brands:")
            print(df['Brand'].value_counts().head(10))

        # Catalogue ID statistics
        if 'Catalogue ID' in df.columns:
            catalogue_count = df['Catalogue ID'].notna().sum()
            total_count = len(df)
            pct = (catalogue_count / total_count * 100) if total_count > 0 else 0
            print(f"\nProducts with Catalogue ID: {catalogue_count}/{total_count} ({pct:.1f}%)")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
