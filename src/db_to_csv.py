# Purpose: This file takes the table created by board_of_dir_table_make.py and converts it to a CSV file to be used
import sqlite3
import pandas as pd
import utility_functions
from datetime import datetime
from pathlib import Path

def convert_db_to_csv(input_file=None, output_csv_file_name=None):
    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prompt the user for the input and output file names if not provided
    if input_file is None:
        input_file = input("Enter the name of the input SQLite database file (without extension if not provided): ")
    
    if output_csv_file_name is None:
        output_csv_file_name = current_timestamp
    
    # Ensure the output file ends with '.csv'
    if not output_csv_file_name.endswith('.csv'):
        output_csv_file_name += '.csv'
    
    # Define the file paths
    root_path = utility_functions.get_root()
    input_path = rf'{input_file}'
    output_path = Path(root_path) / "outputs" / "csv_outputs" / current_timestamp
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(input_path)
    except sqlite3.Error as e:
        print(f"Failed to connect to the database. Error: {e}")
        return
    
    try:
        query = """SELECT ein, state, city, hours_per_week, years_of_service, title, org_name, person_name, total_revenue FROM nonprofit_board_members"""
        df = pd.read_sql_query(query, conn)
        
        # Reorder columns if desired
        desired_order = ['ein', 'person_name', 'org_name', 'title', 'hours_per_week', 
                         'years_of_service', 'total_revenue', 'city', 'state']
        df = df[desired_order]
        
        # Check if 'years_of_service' is in the columns before modifying it
        if 'years_of_service' in df.columns:
            # Modify 'years_of_service' to ensure it's read as text in Excel
            df['years_of_service'] = "'" + df['years_of_service'].astype(str)
        
        # Export to CSV
        df.to_csv(output_path, index=False)
        
        print(f"CSV file created successfully at {output_path}")
    
    except sqlite3.Error as e:
        print(f"An error occurred while querying the database. Error: {e}")
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    convert_db_to_csv()
