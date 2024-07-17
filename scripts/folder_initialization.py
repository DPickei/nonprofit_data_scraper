import os
import assumptions

def main():
    create_folder_structure()

def create_folder_structure():
    # Define the base location from assumptions
    local_folder_location = assumptions.local_folder_location
    
    # Define the paths for the new folders
    nonprofit_raw_data_path = os.path.join(local_folder_location, "nonprofit_raw_data")
    index_files_csv_path = os.path.join(nonprofit_raw_data_path, "index_files_csv")
    xml_files_path = os.path.join(nonprofit_raw_data_path, "xml_files")
    
    # Create the nonprofit_raw_data folder if it doesn't exist
    if not os.path.exists(nonprofit_raw_data_path):
        os.makedirs(nonprofit_raw_data_path)
        print(f"Created folder: {nonprofit_raw_data_path}")
    else:
        print(f"Folder already exists: {nonprofit_raw_data_path}")
    
    # Create the index_files_csv folder if it doesn't exist
    if not os.path.exists(index_files_csv_path):
        os.makedirs(index_files_csv_path)
        print(f"Created folder: {index_files_csv_path}")
    else:
        print(f"Folder already exists: {index_files_csv_path}")
    
    # Create the xml_files folder if it doesn't exist
    if not os.path.exists(xml_files_path):
        os.makedirs(xml_files_path)
        print(f"Created folder: {xml_files_path}")
    else:
        print(f"Folder already exists: {xml_files_path}")



if __name__ == "__main__":
    main()
