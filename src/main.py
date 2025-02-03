import board_of_dir_table_make
import db_to_csv
import json
import sqlite3
import zipfile
import os
import subprocess
import xml.etree.ElementTree as ET
import utility_functions
from pathlib import Path
from datetime import datetime

ROOT_DIR = utility_functions.get_root()

def initialize_db(output_db_path: str):
    # Create or open a database and set up the required tables
    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()
    # Create table for officers with an additional 'ein' column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT,
            title TEXT,
            hours_per_week REAL,
            org_name TEXT,
            year INTEGER,
            total_revenue INTEGER,
            city TEXT,
            state TEXT,
            ein TEXT  -- New column added
        )
    ''')
    conn.commit()
    conn.close()


def insert_officer_data(output_db_path, officers):
    # Insert officer data into the database
    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()
    # Insert each officer entry, including the EIN
    for officer in officers:
        cursor.execute('''
            INSERT INTO officers (person_name, title, hours_per_week, org_name, year, total_revenue, city, state, ein)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            officer['Person Name'], 
            officer['Title'], 
            officer['Hours Per Week'], 
            officer['Org Name'], 
            officer['Year'],
            officer['Total Revenue'], 
            officer['City'], 
            officer['State'],
            officer['ein']  # Insert EIN
        ))
    conn.commit()
    conn.close()


def query_object_id_by_ein(ein_list):
    annual_indexes = Path(ROOT_DIR) / "sql" / "annual_indexes"
    ein_to_object_ids = {}

    for db_file in os.listdir(annual_indexes):
        if not db_file.endswith('.db'):
            continue
        db_file_path = os.path.join(annual_indexes, db_file)
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()

        for ein_input in ein_list:
            # Remove any dashes from the EIN
            processed_ein = ein_input.replace('-', '').strip()

            # Perform the SQL query
            cursor.execute("SELECT object_id FROM data WHERE ein = ?", (processed_ein,))
            results = cursor.fetchall()

            if results:
                if ein_input not in ein_to_object_ids:
                    ein_to_object_ids[ein_input] = []
                for obj_id in results:
                    object_id = str(obj_id[0])
                    ein_to_object_ids[ein_input].append(object_id)
        conn.close()

    # Handle EINs not found in any database
    not_found_eins = [ein for ein in ein_list if ein not in ein_to_object_ids]
    if not_found_eins:
        print(f"The following EINs were not found in any database: {not_found_eins}")

    return ein_to_object_ids  # Return the mapping from EIN to list of object_ids


def find_file(filename, c):
    # Look up the zip file path and internal XML file path from the database.
    c.execute("SELECT zip_file FROM xml_files WHERE file_name=?", (filename,))
    result = c.fetchone()
    if result:
        zip_path = result[0]
        return zip_path
    return None

def extract_specific_file(zip_path, xml_file_name, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extract(xml_file_name, extract_to)
    except (zipfile.BadZipFile, NotImplementedError, KeyError):
        subprocess.run(
            ['7z', 'x', zip_path, f'-o{extract_to}', '-y', xml_file_name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
def extract_officers(xml_file, year, ein):
    # Load XML and parse it
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Namespace is crucial for finding elements
    ns = {'efile': 'http://www.irs.gov/efile'}

    # Extract the org name
    org_name_path = './/efile:Filer/efile:BusinessName/efile:BusinessNameLine1Txt'
    org_name_element = root.find(org_name_path, namespaces=ns)
    org_name = org_name_element.text if org_name_element is not None else "Unknown Org"

    # Extract total revenue
    total_revenue_path = './/efile:TotalRevenueGrp/efile:TotalRevenueColumnAmt'
    total_revenue_element = root.find(total_revenue_path, namespaces=ns)
    total_revenue = total_revenue_element.text if total_revenue_element is not None else "N/A"

    # Extract preparer city and state
    city_path = './/efile:ReturnHeader/efile:PreparerFirmGrp/efile:PreparerUSAddress/efile:CityNm'
    state_path = './/efile:ReturnHeader/efile:PreparerFirmGrp/efile:PreparerUSAddress/efile:StateAbbreviationCd'
    city_element = root.find(city_path, namespaces=ns)
    state_element = root.find(state_path, namespaces=ns)
    city = city_element.text if city_element is not None else "Unknown City"
    state = state_element.text if state_element is not None else "Unknown State"

    # Initialize a list to hold officer data
    officers = []

    # Find all officer entries in the XML
    for officer in root.findall('.//efile:Form990PartVIISectionAGrp', namespaces=ns):
        person_name = officer.find('efile:PersonNm', namespaces=ns)
        title = officer.find('efile:TitleTxt', namespaces=ns)
        hours_per_week = officer.find('efile:AverageHoursPerWeekRt', namespaces=ns)

        # Check if hours_per_week is a valid element and convert to float for comparison
        if hours_per_week is not None and hours_per_week.text:
            try:
                hours = float(hours_per_week.text)
                # Skip adding to the list if hours are greater than 10
                if hours > config.get("max_hours_filter"):
                    continue
            except ValueError:
                # Handle cases where conversion is not possible
                hours = None
        else:
            hours = None

        # Prepare a dictionary to store data
        officer_data = {
            "Person Name": person_name.text if person_name is not None else "N/A",
            "Title": title.text if title is not None else "N/A",
            "Hours Per Week": hours_per_week.text if hours_per_week is not None else "N/A",
            "Org Name": org_name,
            "Year": year,
            "Total Revenue": total_revenue,  # Add the total revenue to the dictionary
            "City": city,  # Add city
            "State": state,  # Add state
            "ein": ein  # Add EIN to the officer data
        }

        # Append the data dictionary to the list (This line must be inside the for loop)
        officers.append(officer_data)

    return officers

    

def gather_and_load_990_data_into_db(ein_to_object_ids, output_db_path):
    # Connect to .db file that gives us the XML file addresses that we'll parse
    mapping_db = Path(ROOT_DIR) / "nonprofit_raw_data" / "zip_address_by_object_id_database.db"
    c = sqlite3.connect(mapping_db).cursor()

    # Connect to the zip folder holding our XML files
    zip_folder_path = Path(ROOT_DIR) / "nonprofit_raw_data" / "xml_files"

    for ein, object_ids in ein_to_object_ids.items():
        for object_id in object_ids:
            year = object_id[:4]  # Extract the year from the object_id or filename as appropriate
            filename = object_id  # Assuming object_id corresponds to filename; adjust if necessary

            if '_public.xml' not in filename:
                filename += "_public.xml"
            zip_file_name = find_file(filename, c)
            if zip_file_name is None:
                print("File not found in any zip file or database.")
                continue
            
            zip_file_path = Path(ROOT_DIR) / "nonprofit_raw_data" / "xml_files" / zip_file_name
            extract_path = os.path.join(zip_folder_path, 'extracted')
            extract_specific_file(zip_file_path, filename, extract_path)
            extracted_xml_path = os.path.join(extract_path, filename)
            
            if os.path.exists(extracted_xml_path):
                officers = extract_officers(extracted_xml_path, year, ein)  # Pass the EIN to the function
                # Insert the officer data into the database
                insert_officer_data(output_db_path, officers)
            else:
                print("XML file not found in extracted data.")
    print(".db file created")


def main(config):
    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_db_path = Path(ROOT_DIR) / "outputs" / "sql_outputs" / current_timestamp
    output_csv_file_name = current_timestamp
    ein_list = config.get("ein_list", None)

    # Find object IDs based on EINs
    ein_to_object_ids = query_object_id_by_ein(ein_list)  # This maps ein to a list of object_ids

    # Create the table to put our data into
    initialize_db(output_db_path)

    # --- Start of ETL process ---

    # Extract 990 data from identified filenames and place into output_db_path (.db) for transformations
    gather_and_load_990_data_into_db(ein_to_object_ids, output_db_path)

    # Transform the .db file created
    board_of_dir_table_make.prep_data(output_db_path)

    # Load output to CSV
    db_to_csv.convert_db_to_csv(output_db_path, output_csv_file_name)

    # --- End of ETL process ---

if __name__ == "__main__":
    config = utility_functions.load_config()
    main(config)
