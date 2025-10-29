"""
Simple wrapper to run ERP extraction with correct environment
"""
import subprocess
import os

# Set working directory
os.chdir(r'C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov')

# Run extraction
subprocess.run(['python', 'scripts\\extract_all_erp_prices.py'])
