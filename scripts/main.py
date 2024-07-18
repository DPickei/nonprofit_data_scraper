# Purpose. This is the main script that will end to end do the following
# 1. Take a database of EINs and find their corresponding object_ids
# 2. Feed those object_ids into a function that will return officer data into a .db file 

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
    # Define input variables depending if the user is using assumptions, command line arguments, or manual entries

    # Input variables if the user enters command line arguments
    if len(sys.argv) == 6 and sys.argv[1] != "assumptions":
        upload_db_or_enter_manually = sys.argv[1]
        output_preference = sys.argv[2]
        # allow the user to use the current datetime as a valid filename, so that they can avoid duplicates when
        # reusing the same command line entry
        if sys.argv[3] == "datetime":
            output_db_path = assumptions.output_db_path
        else:
            output_db_path = os.path.join(assumptions.output_db_path_folder, f"{sys.argv[3]}.db")
        user_entered_eins = [sys.argv[4]]
        if sys.argv[5] == "datetime":
            csv_file_name = assumptions.csv_file_name

    # Input variables if the user wishes to have their assumptions entered
    elif sys.argv[1] == "assumptions":
        upload_db_or_enter_manually = assumptions.upload_db_or_enter_manually
        output_preference = assumptions.output_preference
        output_db_path = assumptions.output_db_path
        user_entered_eins = []
        if len(sys.argv) > 2:
            for ein in sys.argv[2:]:
                user_entered_eins.append(ein)
        else:
            user_entered_eins = assumptions.user_entered_eins
        csv_file_name = assumptions.csv_file_name
        
    # Input variables if the user wishes for manual entry
    else:
        # Ask user how they want to input data
        while True:
            upload_db_or_enter_manually = input("Would you like to enter the EIN or upload a DB file (enter/upload_db): ")
            if upload_db_or_enter_manually != "enter" and upload_db_or_enter_manually != "upload_db":
                print("Answer must be 'enter' or 'upload_db'")
                continue
            else:
                break
        
        # Ask user how they want to output data
        while True:
            output_preference = input("How would you like to receive your output? (modified_.db, raw_.db, csv): ")
            if output_preference != "raw_.db" and output_preference != "csv" and output_preference != "modified_.db":
                print("Output preference must be one of the following: raw_.db, modified_.db, or csv")
                continue
            else:
                break

        # Initialize the output database
        output_db_path_folder = assumptions.output_db_path_folder
        output_db_path_name = input("Enter the name of the database you'd like to make (.db): ")
        output_db_path_name = "\\" + output_db_path_name
        if not output_db_path_name.endswith(".db"):
            output_db_path_name += ".db"
        output_db_path = output_db_path_folder + output_db_path_name
        
        # Let the user decide what .db file they want to pull EINs from
        if upload_db_or_enter_manually == "upload_db":
            recreational_nonprofit_eins_file_name = input("Enter the name of the file you'd like to pull EINs from: ")
            recreational_nonprofit_eins_file_name = "\\" + recreational_nonprofit_eins_file_name
            if not recreational_nonprofit_eins_file_name.endswith(".db"):
                recreational_nonprofit_eins_file_name += ".db"
            recreational_nonprofit_eins_path = os.path.join(assumptions.output_db_path_folder, recreational_nonprofit_eins_file_name)
        else:
            user_entered_eins = []
            print('Type esc or exit to end entries')
            while True:
                entry = input('EIN: ')
                if entry == 'esc' or entry == 'exit':
                    break
                else:
                    user_entered_eins.append(entry)
        
        # Establish name of outputted CSV file if desired
        if output_preference == "csv":
            csv_file_name = input("Enter the name of the output CSV file: ")

    # Initialize database with officer table
    initialize_db(output_db_path)

    # Establish path to index
    ein_db_path = assumptions.db_index_path  # Changed from assumptions.ein_db_path to assumptions.db_index_path
        
    # Get the object ids by querying with EINs from your database of nonprofit EINs
    if upload_db_or_enter_manually == 'upload_db':
        filenames = query_object_id_by_ein(ein_db_path, recreational_nonprofit_eins_path, upload_db_or_enter_manually)
    else:
        # Get the object ids by querying with EINs entered from the user
        filenames = query_object_id_by_ein(ein_db_path, user_entered_eins, upload_db_or_enter_manually)

    # Start XML parsing through each obj_id returned
    for filename in filenames:
        print("Filename:", filename)
        year = filename[:4]  # Extract the year from the filename
        if '_public.xml' not in filename:
            filename += "_public.xml"
        zip_file_path, xml_file_path = find_file(filename)
        
        if zip_file_path and xml_file_path:
            extract_path = os.path.join(zip_folder_path, 'extracted')
            extract_specific_file(zip_file_path, xml_file_path, extract_path)
            extracted_xml_path = os.path.join(extract_path, xml_file_path)
            
            if os.path.exists(extracted_xml_path):
                print(f"Found XML file: {extracted_xml_path}")
                officers = extract_officers(extracted_xml_path, year)  # Pass the year to the function
                print("Officers Found")
                # Within your main logic:
                insert_officer_data(output_db_path, officers)
                print("Successfully uploaded to database")
            else:
                print("XML file not found in extracted data.")
        else:
            print("File not found in any zip file or database.")

    # Modify officers table to board_of_dir_table_make so it can be loaded to a CSV in the right format
    if output_preference == "csv" or output_preference == "modified_.db":
        board_of_dir_table_make.main(output_db_path)
        print("Modified .db created")

    # Output to CSV if requested by user
    if output_preference == "csv":
        db_to_csv.main(output_db_path, csv_file_name)
        print("CSV created")


def initialize_db(output_db_path):
    """Create or open a database and set up the required tables."""
    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()
    # Create table for officers
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
            state TEXT
        )
    ''')
    conn.commit()
    conn.close()


def insert_officer_data(output_db_path, officers):
    """Insert officer data into the database."""
    print(f"Output_db_path: {output_db_path}")
    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()
    # Insert each officer entry
    for officer in officers:
        cursor.execute('''
            INSERT INTO officers (person_name, title, hours_per_week, org_name, year, total_revenue, city, state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (officer['Person Name'], officer['Title'], officer['Hours Per Week'], officer['Org Name'], officer['Year'],
               officer['Total Revenue'], officer['City'], officer['State']))
    conn.commit()
    conn.close()

def query_object_id_by_ein(ein_db_path, recreational_nonprofit_eins_path, upload_db_or_enter_manually):
    if upload_db_or_enter_manually == "upload_db":
        # Connect to the SQLite database to fetch all EINs
        conn_eins = sqlite3.connect(recreational_nonprofit_eins_path)
        cursor_eins = conn_eins.cursor()
        cursor_eins.execute("SELECT ein FROM organizations")
        eins_as_ints = [item[0] for item in cursor_eins.fetchall()]
        conn_eins.close()
        
        # Convert each integer to a string using map
        eins = list(map(str, eins_as_ints))

        # Count number of EINs so we know the max amount
        total_eins = len(eins)

        # Prompt the user for the number of EINs to parse
        while True:
            desired_ein_amount = (
                input(
                    f"Select quantity of EINs to parse (enter 'all' to retrieve all, max {total_eins}): "
                ).strip().lower()
            )
            if desired_ein_amount == 'all':
                limit = None
                break
            elif desired_ein_amount.isdigit():
                limit = int(desired_ein_amount)
                if limit <= total_eins:
                    break
                else:
                    print(f"Error: Too high of a value, there are only {total_eins} EINs in the database.")
            else:
                print("Invalid input. Please enter a number or 'all'.")
    
    else:
        # Using this value which has no place for the EIN specific search to function as the ein value
        eins = recreational_nonprofit_eins_path
        limit = None

    # Connect to the SQLite database to query object_ids
    object_ids = []

    # Counter to reference EINs counted
    ein_counter = 0

    for db_file in os.listdir(ein_db_path):
        if db_file.endswith('.db'):
            db_file_path = os.path.join(ein_db_path, db_file)
            conn = sqlite3.connect(db_file_path)
            cursor = conn.cursor()

            for ein_input in eins:
                # Remove any dashes from the EIN
                processed_ein = ein_input.replace('-', '')
                print("Processed EIN:", processed_ein)

                # Perform the SQL query
                cursor.execute("SELECT object_id FROM data WHERE ein = ?", (processed_ein,))
                results = cursor.fetchall()

                # Check if any results were found
                if results:
                    print("Object IDs found:")
                    for obj_id in results:
                        object_ids.append(str(obj_id[0]))
                else:
                    print("No results found for the given EIN.")

                # Check if EIN limit is reached
                ein_counter += 1
                try:
                    if limit and limit < ein_counter and upload_db_or_enter_manually == "upload_db":
                        break
                except TypeError:
                    continue

            # Close the connection to the current DB file
            conn.close()

            if limit and limit < ein_counter:
                break

    # Return the list of object IDs
    return object_ids


# Define paths
obj_id_db_path = assumptions.obj_id_db_path
zip_folder_path = assumptions.zip_folder_path

# Connect to SQLite database
conn = sqlite3.connect(obj_id_db_path)
c = conn.cursor()

# Ensure the correct table is created
c.execute('''CREATE TABLE IF NOT EXISTS xml_files (file_name TEXT, file_address TEXT)''')

def find_file(filename):
    """Look up the zip file path and internal XML file path from the database."""
    c.execute("SELECT file_address FROM xml_files WHERE file_name=?", (filename,))
    result = c.fetchone()
    if result:
        # Assuming the file_address format is 'zip_path\\xml_file_path'
        full_path = result[0]
        zip_path, xml_file_path = os.path.split(full_path)
        return zip_path, xml_file_path
    return None, None

def extract_specific_file(zip_path, xml_file_path, extract_to):
    """Extract a specific file from a zip archive."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extract(xml_file_path, extract_to)
            print("File extracted successfully with zipfile.")
    except (zipfile.BadZipFile, NotImplementedError):
        print("Using 7-Zip due to unsupported compression method or bad zip file.")
        subprocess.run(['7z', 'x', zip_path, f'-o{extract_to}', f'-y', f'{xml_file_path}'], check=True)


def extract_officers(xml_file, year):
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
            "State": state  # Add state
        }

        # Append the data dictionary to the list
        officers.append(officer_data)

    return officers    


if __name__ == "__main__":
    main()
