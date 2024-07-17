# Purpose: A single place to place all assumptions and local file paths

import os
from datetime import datetime

# Establish current datetime
current_datetime = datetime.now()
current_datetime = current_datetime.strftime("%Y%m%d_%H%M%S")

# Local folder location (enter the folder address where this clone is stored)
local_folder_location = r'C:\Users\dwpic\Documents\Coding\Projects'
local_data_location = os.path.join(local_folder_location, "nonprofit_raw_data")

# Pathing assumptions
project_folder_location = os.path.join(local_folder_location, "nonprofit_data_scraper")
zip_folder_path = os.path.join(local_data_location, "xml_files")
csv_index_path = os.path.join(local_data_location, "index_files_csv")
obj_id_db_path = os.path.join(local_data_location, "zip_address_by_object_id_database.db")
ein_db_path = os.path.join(project_folder_location, "sql", "index_master.db")
db_index_path = os.path.join(project_folder_location, "sql", "annual_indexes")

# Project folder locations (Do not touch unless you want to modify core code)
output_db_path_folder = os.path.join(project_folder_location, "outputs", "sql_outputs")

# Input variables. Edit these as you wish
max_hours = 12 # Will filter out anybody with more than the max_hours listed
upload_db_or_enter_manually = "enter"
output_preference = "csv"
output_db_path = os.path.join(output_db_path_folder, f"{current_datetime}.db")
user_entered_eins = [
    #enter values as a string. Eg., "131737538"
    "131737538"
]
csv_file_name = current_datetime