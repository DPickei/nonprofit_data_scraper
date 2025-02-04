# Purpose: This script converts publicly available CSV files into .db files
# Reason: This is so we can match EINs to Obj IDs, which will allow us to locate XML files
import os
import pandas as pd
import sqlite3
import utility_functions
from pathlib import Path

def convert_csv_to_db():
    root_path = utility_functions.get_root()
    config = utility_functions.load_config()

    annual_filings_csv = Path(root_path) / config.get("pathing").get("annual_filings_csv")
    annual_filings_db = Path(root_path) / config.get("pathing").get("annual_filings_db")

    if annual_filings_db.stat().st_size == 0:
        print("Annual filings database does not exist. Creating them from csv files")
    else:
        return
    
    if annual_filings_csv.stat().st_size == 0:
        print(f"Please download index files for years you wish to find xml files for. See https://www.irs.gov/charities-non-profits/form-990-series-downloads for files and download them to {annual_filings_csv}")
        exit(1)

    print("Making annual_filings database")
    
    # Ensure the annual_filings_db directory exists
    if not os.path.exists(annual_filings_db):
        os.makedirs(annual_filings_db)
        print(f"Created directory: {annual_filings_db}")
    else:
        print(f"Directory exists: {annual_filings_db}")

    # Get the list of CSV files and existing DB files in the annual_filings_db folder
    csv_files = [f for f in os.listdir(annual_filings_csv) if f.endswith('.csv')]
    db_files = [f for f in os.listdir(annual_filings_db) if f.endswith('.db')]
    
    print(f"Found {len(csv_files)} CSV files in {annual_filings_csv}")
    print(f"Found {len(db_files)} DB files in {annual_filings_db}")

    # Process each CSV file
    for csv_file in csv_files:
        db_file_name = csv_file.replace('.csv', '.db')

        if db_file_name in db_files:
            print(f"Skipping {csv_file} as corresponding DB file already exists in annual_filings_db.")
            continue

        csv_path = os.path.join(annual_filings_csv, csv_file)
        db_path = os.path.join(annual_filings_db, db_file_name)

        print(f"Processing {csv_file}...")

        # Read the CSV file into a DataFrame
        try:
            df = pd.read_csv(csv_path)
            print(f"Read {csv_file} with {len(df)} rows.")
        except Exception as e:
            print(f"Failed to read {csv_file}: {e}")
            continue

        # Ensure EIN values are 9 digits
        if 'EIN' in df.columns:
            df['EIN'] = df['EIN'].apply(lambda x: f"{int(x):09d}")
            print("Formatted EIN values to 9 digits.")

        # Drop the specified columns
        columns_to_remove = ['RETURN_ID', 'FILING_TYPE', 'TAX_PERIOD', 'SUB_DATE', 'TAXPAYER_NAME', 'RETURN_TYPE', 'DLN']
        df = df.drop(columns=columns_to_remove, errors='ignore')
        print(f"Dropped columns: {columns_to_remove}")

        # Rename columns to match the schema
        df.columns = [col.lower() for col in df.columns]  # optional, based on your requirements

        # Create the SQLite database and write the DataFrame to it
        try:
            with sqlite3.connect(db_path) as conn:
                df.to_sql('data', conn, if_exists='replace', index=False, chunksize=25000)
                
                # Print progress for large DataFrame
                if len(df) > 25000:
                    for i in range(0, len(df), 25000):
                        print(f"Inserted {i + 25000} rows into {db_file_name}")

                # Create the required schema and indexes
                create_schema_query = '''
                CREATE TABLE IF NOT EXISTS "data" (
                    ein INTEGER,
                    taxpayer_name TEXT,
                    object_id INTEGER
                );
                CREATE INDEX IF NOT EXISTS ein_index ON data (ein);
                CREATE INDEX IF NOT EXISTS object_id_index ON data (object_id);
                '''
                conn.executescript(create_schema_query)
                print(f"Created table and indexes in {db_file_name}")

            print(f"Converted {csv_file} to {db_file_name}")
        except Exception as e:
            print(f"Failed to write to database {db_file_name}: {e}")

if __name__ == "__main__":
    convert_csv_to_db()
