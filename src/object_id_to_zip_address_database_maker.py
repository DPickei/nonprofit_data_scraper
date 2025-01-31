# This script will index all of the addresses of the XML files by their name. This only needs to be done once
# If you need to repeat this script. Delete the previous file (sql\"zip_address_by_object_id_database.db") before executing

import assumptions
import sqlite3
import os
import zipfile

# Define the directory with zip files and the database path
zip_directory = os.path.join(assumptions.zip_folder_path)
database_path = assumptions.obj_id_db_path

# Connect to SQLite database
conn = sqlite3.connect(database_path)
c = conn.cursor()

# Create table
c.execute('''
CREATE TABLE IF NOT EXISTS xml_files (
    file_name TEXT,
    file_address TEXT
)
''')

# Function to add file to the database
def add_file_to_db(file_name, file_address):
    c.execute("INSERT INTO xml_files (file_name, file_address) VALUES (?, ?)", (file_name, file_address))

# Get total number of zip files
total_zips = len([name for name in os.listdir(zip_directory) if name.endswith('.zip')])
processed_zips = 0

# Loop through each zip file in the directory
for zip_file in os.listdir(zip_directory):
    if zip_file.endswith('.zip'):
        zip_path = os.path.join(zip_directory, zip_file)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all XML files and add them to the database
            xml_files = [xml_file for xml_file in zip_ref.namelist() if xml_file.endswith('.xml')]
            total_xml_files = len(xml_files)
            processed_xml_files = 0

            for xml_file in xml_files:
                add_file_to_db(xml_file, f"{zip_path}\\{xml_file}")
                processed_xml_files += 1
                if processed_xml_files % 10000 == 0:  # Adjust the modulus value based on the total count of files
                    print(f"Processed {processed_xml_files}/{total_xml_files} XML files in {zip_file}")

        processed_zips += 1
        print(f"Completed {processed_zips}/{total_zips} zip files.")

# Commit changes and close the connection
conn.commit()
conn.close()

print("Database has been created and XML file paths have been indexed.")
