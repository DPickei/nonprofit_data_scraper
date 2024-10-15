# Purpose: Core logic to execute the following
# 1. Take EINs provided by the user
# 2. Output personnel information of the board for each EIN

import sys
import assumptions
import board_of_dir_table_make
import db_to_csv
import sqlite3
import zipfile
import os
import subprocess
import xml.etree.ElementTree as ET

def main():
    # See if the user would like to manually enter values or use 'assumptions.py'
    condition = get_user_input_preference()
    
    # Declare values for input variables
    db_or_manual_entry = determine_ein_source(condition)
    output_preference = determine_output_preference(condition)
    output_db_path = make_sql_output_file(condition)
    output_csv_file_name = make_csv_output_file(condition, output_preference)
    ein_list = gather_eins(condition, db_or_manual_entry)

    # Find object IDs based on EINs
    ein_to_object_ids = query_object_id_by_ein(ein_list)  # This maps ein to a list of object_ids

    # Create the table to put our data into
    initialize_db(output_db_path)

    # --- Start of ETL process ---

    # Extract 990 data from identified filenames and place into output_db_path (.db) for transformations
    gather_and_load_990_data_into_db(ein_to_object_ids, output_db_path)

    # Transform the .db file created
    board_of_dir_table_make.main(output_db_path)

    # Load output to CSV if requested by user
    if output_preference in ["csv", "both"]:
        db_to_csv.main(output_db_path, output_csv_file_name)

    # --- End of ETL process ---

    # Delete the .db file if the user has specified just for a CSV file returned
    if output_preference == "csv":
        os.remove(output_db_path)


def get_user_input_preference():
    if len(sys.argv) == 1:
        condition = "input_asked"
    elif len(sys.argv) > 1 and sys.argv[1] == "assumptions":
        condition = "input_from_assumptions"
    else:
        print("invalid entry")
        sys.exit()
    return condition


def determine_ein_source(condition):
    if condition == "input_asked":
        while True:
            db_or_manual_entry = input("Would you like to enter the EIN or upload a DB file (enter/upload): ")
            if db_or_manual_entry != "enter" and db_or_manual_entry != "upload":
                print("Answer must be 'enter' or 'upload'")
                continue
            else:
                break
    elif condition == "input_from_assumptions":
        db_or_manual_entry = assumptions.db_or_manual_entry
    return db_or_manual_entry

def determine_output_preference(condition):
    if condition == "input_asked":
        while True:
            output_preference = input("How would you like to receive your output? (sql, csv, both): ")
            if output_preference not in ["sql", "csv", "both"]:
                print("Output preference must be one of the following: 'sql', 'csv', or 'both'")
                continue
            else:
                break
    elif condition == "input_from_assumptions":
        output_preference = assumptions.output_preference
    return output_preference


def make_sql_output_file(condition):
    if condition == "input_asked":
        output_db_path_folder = assumptions.output_db_path_folder
        output_db_path_name = input("Enter the name of the database (.db file) you'd like to make. Use 'datetime' for current datetime: ")
        if output_db_path_name == "datetime":
            output_db_path_name = assumptions.current_datetime
        output_db_path_name = "\\" + output_db_path_name
        if not output_db_path_name.endswith(".db"):
            output_db_path_name += ".db"
        output_db_path = output_db_path_folder + output_db_path_name
    elif condition == "input_from_assumptions":
        output_db_path = assumptions.output_db_path
    return output_db_path


def make_csv_output_file(condition, output_preference):
    if condition == "input_asked" and output_preference in ["csv", "both"]:
        output_csv_file_name = input("Enter the name of the output CSV file. Use 'datetime' for current datetime: ")
        if output_csv_file_name == "datetime":
            output_csv_file_name = assumptions.current_datetime
    elif condition == "input_from_assumptions":
        output_csv_file_name = assumptions.output_csv_file_name
    return output_csv_file_name


def gather_eins(condition, db_or_manual_entry):
    ein_list = []
    if condition == "input_asked" and db_or_manual_entry == "enter":
        print('Type esc or exit to end entries')
        while True:
            entry = input('EIN: ')
            if entry == 'esc' or entry == 'exit':
                print("ein list: ", ein_list)
                break
            elif ',' in entry:
                entries = entry.split(',')
                for ein in entries:
                    ein_list.append(ein)
            else:
                ein_list.append(entry)
    elif condition == "input_asked" and db_or_manual_entry == "upload":
        while True:
            ein_db_file = input("Enter the name of the .db file to upload EINs from. Please make sure this file exists within 'sql > ein_db' : ")
            if not ein_db_file.endswith(".db"):
                ein_db_file += ".db"
            ein_db_file_path = os.path.join(assumptions.ein_db_path, ein_db_file)
            if not os.path.exists(ein_db_file_path):
                print("File does not exist. Please try again.")
            else:
                break
        ein_list = get_eins_from_db(ein_db_file_path)
    elif condition == "input_from_assumptions" and db_or_manual_entry == "enter":
        if len(sys.argv) > 2:
            ein_list = sys.argv[2:]
        else:
            ein_list = assumptions.ein_list
    elif condition == "input_from_assumptions" and db_or_manual_entry == "upload":
        ein_list = get_eins_from_db(assumptions.ein_db_file)
    return ein_list


def get_eins_from_db(ein_db_file):
    # Connect to the SQLite database
    conn = sqlite3.connect(ein_db_file)
    cursor = conn.cursor()

    # Query the 'ein' column from the 'organizations' table
    cursor.execute("SELECT ein FROM organizations")
    eins = [row[0] for row in cursor.fetchall()]

    # Close the database connection
    conn.close()

    return eins

    
def initialize_db(output_db_path):
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
    annual_indexes = assumptions.annual_indexes  # Directory containing .db files
    ein_to_object_ids = {}  # Dictionary to map ein to a list of object_ids

    for db_file in os.listdir(annual_indexes):
        if db_file.endswith('.db'):
            db_file_path = os.path.join(annual_indexes, db_file)
            print(f"Processing database file: {db_file_path}")
            conn = sqlite3.connect(db_file_path)
            cursor = conn.cursor()

            for ein_input in ein_list:
                # Remove any dashes from the EIN
                processed_ein = ein_input.replace('-', '').strip()
                print(f"Processed EIN: {processed_ein}")

                # Perform the SQL query
                cursor.execute("SELECT object_id FROM data WHERE ein = ?", (processed_ein,))
                results = cursor.fetchall()

                if results:
                    print(f"Object IDs found for EIN {processed_ein}: {[obj_id[0] for obj_id in results]}")
                    # Initialize the list if the EIN is encountered for the first time
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
    c.execute("SELECT file_address FROM xml_files WHERE file_name=?", (filename,))
    result = c.fetchone()
    if result:
        # Assuming the file_address format is 'zip_path\\xml_file_path'
        full_path = result[0]
        zip_path, xml_file_path = os.path.split(full_path)
        return zip_path, xml_file_path
    return None, None

def extract_specific_file(zip_path, xml_file_path, extract_to):
    # Extract a specific file from a zip archive
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extract(xml_file_path, extract_to)
            print("File extracted successfully with zipfile.")
    except (zipfile.BadZipFile, NotImplementedError):
        print("Using 7-Zip due to unsupported compression method or bad zip file.")
        subprocess.run(['7z', 'x', zip_path, f'-o{extract_to}', f'-y', f'{xml_file_path}'], check=True)


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
                if hours > assumptions.max_hours:
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
    c = sqlite3.connect(assumptions.obj_id_db_path).cursor()

    # Connect to the zip folder holding our XML files
    zip_folder_path = assumptions.zip_folder_path

    for ein, object_ids in ein_to_object_ids.items():
        for object_id in object_ids:
            print(f"Processing Object ID: {object_id} for EIN: {ein}")
            year = object_id[:4]  # Extract the year from the object_id or filename as appropriate
            filename = object_id  # Assuming object_id corresponds to filename; adjust if necessary

            if '_public.xml' not in filename:
                filename += "_public.xml"
            zip_file_path, xml_file_path = find_file(filename, c)
            
            if zip_file_path and xml_file_path:
                extract_path = os.path.join(zip_folder_path, 'extracted')
                extract_specific_file(zip_file_path, xml_file_path, extract_path)
                extracted_xml_path = os.path.join(extract_path, xml_file_path)
                
                if os.path.exists(extracted_xml_path):
                    print(f"Found XML file: {extracted_xml_path}")
                    officers = extract_officers(extracted_xml_path, year, ein)  # Pass the EIN to the function
                    print("Officers Found")
                    # Insert the officer data into the database
                    insert_officer_data(output_db_path, officers)
                    print("Successfully uploaded to database")
                else:
                    print("XML file not found in extracted data.")
            else:
                print("File not found in any zip file or database.")
    print(".db file created")



if __name__ == "__main__":
    main()
