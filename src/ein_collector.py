import requests
import sqlite3
import utility_functions
from pathlib import Path

def collect_eins():
    nonprofit_type = input("Enter the type of nonprofit you'd like to retrieve EINs for. E.g., for a 501(c)(4) nonprofit, enter '4': ")
    filename = input("Enter the filename to store the EINs: ") + ".db"
    max_eins_to_retrieve = min(int(input("Enter the number of EINs you'd like to retrieve (up to 10,000): ")), 10000)
    root_path = utility_functions.get_root()
    database_path = Path(root_path) / "sql" / "ein_db" / filename

    create_database(database_path)
    fetch_and_store_eins(nonprofit_type, database_path, max_eins_to_retrieve)

def create_database(database_path):
    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS organizations (ein TEXT UNIQUE)''')
    conn.commit()
    conn.close()

def fetch_and_store_eins(nonprofit_type, database_path, max_eins_to_retrieve):
    conn = sqlite3.connect(database_path)
    c = conn.cursor()

    api_url = 'https://projects.propublica.org/nonprofits/api/v2/search.json'
    params = {'c_code[id]': nonprofit_type, 'page': 0}
    continue_fetching = True

    total_collected = 0  # Track the total number of EINs collected

    while continue_fetching and total_collected < max_eins_to_retrieve:
        response = requests.get(api_url, params=params)
        if response.status_code == 400 and "Pagination out of range" in response.text:
            print("Reached the end of available data or pagination limit.")
            break
        elif response.status_code != 200:
            print("Failed to fetch data:", response.status_code, response.text)
            break

        data = response.json()
        if 'organizations' not in data:
            print("No more organizations data available or error in response.")
            break

        for org in data['organizations']:
            if total_collected >= max_eins_to_retrieve:
                continue_fetching = False
                break
            ein = str(org['ein'])  # Ensure EIN is treated as a string
            ein = ein.zfill(9)  # Prefix with zeros to ensure EIN is 9 characters long
            # print(f"Fetched EIN: {ein}")  # Debug: print the EIN to verify
            c.execute('INSERT OR IGNORE INTO organizations (ein) VALUES (?)', (ein,))
            total_collected += 1

            # Print progress for every 25 EINs collected
            if total_collected % 25 == 0:
                print(f"{total_collected}/{max_eins_to_retrieve} EINs collected")

        conn.commit()
        if total_collected < max_eins_to_retrieve:
            params['page'] += 1

    conn.close()


if __name__ == "__main__":
    collect_eins()
