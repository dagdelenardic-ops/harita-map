import pandas as pd
import sys

file_path = '/Users/gurursonmez/Documents/Harita/data/public_emdat_2026-01-27.xlsx'
print(f"Reading {file_path}...")
try:
    df = pd.read_excel(file_path)
    print("Columns:", df.columns.tolist())
    print("-" * 20)
    print("First 3 rows:")
    print(df.head(3).to_string())
except Exception as e:
    print(f"Error reading excel: {e}")
