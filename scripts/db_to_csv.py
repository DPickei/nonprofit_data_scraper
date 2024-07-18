# Purpose: This file takes the table created by board_of_dir_table_make.py and converts it to a CSV file to be used

import assumptions
import os
import sqlite3
import pandas as pd

def main(input_file=None, csv_file_name=None):

    # Prompt the user for the input and output file names if not provided
    if input_file is None:
        input_file = input("Enter the name of the input SQLite database file (without extension if not provided): ")
    if csv_file_name is None:
        csv_file_name = input("Enter the name of the output CSV file (without extension if not provided) Example format - 5.22.2024_additional_uploads: ")

    # Ensure the output file ends with '.csv'
    if not csv_file_name.endswith('.csv'):
        csv_file_name += '.csv'

    # Define the file paths
    input_path = rf'{input_file}'
    output_path = os.path.join(assumptions.output_csv_path_folder, csv_file_name)

    # Connect to the SQLite database
    conn = sqlite3.connect(input_path)

    # Query the database to select all from your table
    query = ("""SELECT state, city, hours_per_week, years_of_service, title, org_name, person_name
             FROM nonprofit_board_members""")
    df = pd.read_sql_query(query, conn)

    # Check if 'years_of_service' is in the columns before modifying it
    if 'years_of_service' in df.columns:
        # Modify 'years_of_service' to ensure it's read as text in Excel
        df['years_of_service'] = "'" + df['years_of_service'].astype(str)

    # Export to CSV
    df.to_csv(output_path, index=False)

    # Close the connection


if __name__ == "__main__":
    main()