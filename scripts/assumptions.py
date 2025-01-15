# Purpose: A single place to store user inputs and files addresses

import os
from datetime import datetime

# Establish current datetime
current_datetime = datetime.now()
current_datetime = current_datetime.strftime("%Y%m%d_%H%M%S")

# --- USER INPUTS: Only make edits to this section unless you are comfortable changing core logic of this program

local_folder_location = r'C:\Users\dwpic\Documents\Coding\Projects' # E.g., r'C:\Users\David\Documents\Projects'

max_hours = 12 # I.e., Anybody on a nonprofit with 40 hours will be excluded if max_hours is 12

db_or_manual_entry = "enter" # Options are: "enter" and "upload". Upload will reference a specified .db file in
# sql > ein_db. Ensure the column of the .db file is name "ein" and is in a table named "organizations". enter
# will use ein_list (list located in this file) as reference for EINs to parse

ein_file_name = "example_storage.db" # If you choose "upload" for db_or_manual_entry, this will specify the .db file
                                  # to extract EINs from

output_preference = "both" # This determines how the parsed data is stored. Options are: "csv", "sql", and "both"

output_db_file_name = current_datetime # Filename option for the created .db file. Use 'datetime' for current datetime.

output_csv_file_name = current_datetime # Filename option for the created csv file. Use 'datetime' for current datetime.

ein_list = [ # This is an option of where to place EINs for parsing. Enter EINs as string values.
             # To find the EIN of a nonprofit. Enter the nonprofit name at 'https://projects.propublica.org/nonprofits/'
             # Locate header of the nonprofit profile page and copy into the list values
    "230969420,590198160,592799884,430494275,230969350,941748806,560685943,592118294,060607166,510042264"
]

# -- END OF USER INPUTS


# Pathing assumptions

# Base locations
local_data_location = os.path.join(local_folder_location, "nonprofit_raw_data")
project_folder_location = os.path.join(local_folder_location, "nonprofit_data_scraper")

# Local data paths
zip_folder_path = os.path.join(local_data_location, "xml_files")
csv_index_path = os.path.join(local_data_location, "index_files_csv")
obj_id_db_path = os.path.join(local_data_location, "zip_address_by_object_id_database.db")

# Project SQL paths
ein_db_path = os.path.join(project_folder_location, "sql", "ein_db")
annual_indexes = os.path.join(project_folder_location, "sql", "annual_indexes")

# Specific output files
output_csv_path_folder = os.path.join(project_folder_location, "outputs", "csv_outputs")
output_db_path_folder = os.path.join(project_folder_location, "outputs", "sql_outputs")
ein_db_file = os.path.join(ein_db_path, ein_file_name)
output_db_path = os.path.join(output_db_path_folder, f"{output_db_file_name}.db")
