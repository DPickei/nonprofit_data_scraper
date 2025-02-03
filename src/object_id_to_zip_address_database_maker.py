import sqlite3
import zipfile
import utility_functions
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent  


def create_zip_address_db():
    config = utility_functions.load_config()
    zip_directory = Path(ROOT_DIR) / config.get("pathing").get("xml_files")
    database_path = Path(ROOT_DIR) / config.get("pathing").get("zip_address_by_object_id_database")

    if database_path.is_file() is False:
        print(f"No database found. Making a map of file paths from object IDs at: {database_path}")
    else:
        return

    # Open the database connection once
    conn = sqlite3.connect(database_path)
    c = conn.cursor()

    # Create the table once
    c.execute('''
        CREATE TABLE IF NOT EXISTS xml_files (
            file_name TEXT PRIMARY KEY,
            zip_file TEXT
        )
    ''')
    conn.commit()

    # Get all zip files using pathlib's globbing (more Pythonic)
    zip_files = list(zip_directory.glob("*.zip"))
    total_zips = len(zip_files)
    processed_zips = 0

    for zip_file in zip_files:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            # Filter XML files within the zip
            xml_files = [xml_file for xml_file in zip_ref.namelist() if xml_file.endswith('.xml')]
            total_xml_files = len(xml_files)
            processed_xml_files = 0

            # Accumulate rows to insert
            rows = []
            for xml_file in xml_files:
                rows.append((xml_file, zip_file.name))
                processed_xml_files += 1

                # Optional: print progress every 10,000 files
                if processed_xml_files % 10000 == 0:
                    print(f"Accumulated {processed_xml_files}/{total_xml_files} XML files in {zip_file.name}")

            # Bulk insert rows; using "INSERT OR IGNORE" if duplicate file names are possible
            c.executemany("INSERT OR IGNORE INTO xml_files (file_name, zip_file) VALUES (?, ?)", rows)
            conn.commit()

        processed_zips += 1
        print(f"Completed {processed_zips}/{total_zips} zip files.")

    conn.close()
    print("Database has been created and XML file paths have been indexed.")

if __name__ == "__main__":
    create_zip_address_db()
