from pathlib import Path


def make_file_if_not_exists(file: str):
    file_path = Path(file)
    if not file_path.exists():
        file_path.mkdir(parents=True)
        print(f"Created folder: {file}")
    else:
        print(f"Folder already exists: {file}")


def main():
    # Define the paths for the new folders
    nonprofit_raw_data_path = "nonprofit_raw_data"
    index_files_csv_path = Path(nonprofit_raw_data_path) / "index_files_csv"
    xml_files_path = Path(nonprofit_raw_data_path) / "xml_files"
    
    # Create the nonprofit_raw_data folder if it doesn't exist
    make_file_if_not_exists(nonprofit_raw_data_path)
    make_file_if_not_exists(index_files_csv_path)
    make_file_if_not_exists(xml_files_path)


if __name__ == "__main__":
    main()
