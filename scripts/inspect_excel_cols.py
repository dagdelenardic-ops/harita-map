import pandas as pd
file_path = '/Users/gurursonmez/Documents/Harita/data/public_emdat_2026-01-27.xlsx'
try:
    df = pd.read_excel(file_path, nrows=0) # Read only header
    print("ALL COLUMNS:")
    for col in df.columns:
        print(col)
except Exception as e:
    print(e)
