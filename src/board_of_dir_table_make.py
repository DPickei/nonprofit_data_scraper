# board_of_dir_table_make.py
# Purpose: This function will take the raw output of main.py and turn it into a db that can be converted to a csv file

import sqlite3
import os
import json

# Load config.json from the parent directory (assuming 'scripts' is inside the root)
config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
with open(config_file_path, 'r') as file:
    config = json.load(file)

BATCH_SIZE = config["BATCH_SIZE"]  # Moved from a hard-coded value to the config

def main(database_path=None):
    if database_path is None:
        input_file = input("Enter the name of the file you'd like to modify: ")
        if not input_file.endswith(".db"):
            input_file += ".db"
        database_path = input_file

    conn = sqlite3.connect(database_path)
    conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode
    cursor = conn.cursor()

    # Ensure the new table exists and is correctly configured
    create_table(cursor)

    # Normalize existing data and show progress
    normalize_data(cursor, conn)

    # Index data to improve run speed
    create_indexes(cursor)

    # Insert data into the new table with duplicate check and show progress
    populate_nonprofit_board_members(cursor, conn)

    # Remove duplicates post-insertion
    remove_duplicates(cursor)

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print("Database cleaned successfully.")


def normalize_data(cursor, conn):
    """Convert data to a consistent format and show progress."""
    total_rows = cursor.execute('SELECT COUNT(*) FROM nonprofit_board_members').fetchone()[0]
    for start in range(0, total_rows, BATCH_SIZE):
        cursor.execute(f'''
            UPDATE nonprofit_board_members
            SET person_name = UPPER(person_name), title = UPPER(title), org_name = UPPER(org_name), city = UPPER(city), state = UPPER(state)
            WHERE id BETWEEN {start} AND {start + BATCH_SIZE - 1}
        ''')
        conn.commit()  # Commit after each batch to ensure changes are saved
        print(f"Normalization in progress. Processed rows {start + 1} to {min(start + BATCH_SIZE, total_rows)}.")

    print(f"Normalization complete. {total_rows} rows processed.")


def create_table(cursor):
    """Drop and recreate the table to reset with correct UNIQUE constraints."""
    cursor.execute('DROP TABLE IF EXISTS nonprofit_board_members')
    cursor.execute('''
        CREATE TABLE nonprofit_board_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT,
            title TEXT,
            hours_per_week REAL,
            org_name TEXT,
            years_of_service TEXT,
            total_revenue INTEGER,
            city TEXT,
            state TEXT,
            ein TEXT,  -- New column added
            UNIQUE(person_name, org_name, years_of_service, ein)  -- Updated UNIQUE constraint
        )
    ''')
    print("Table recreated successfully.")


def create_indexes(cursor):
    """Create indexes to improve query performance."""
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_person_name ON nonprofit_board_members (person_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_org_name ON nonprofit_board_members (org_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_years_of_service ON nonprofit_board_members (years_of_service)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_city ON nonprofit_board_members (city)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_state ON nonprofit_board_members (state)')
    print("Indexes created successfully.")


def remove_duplicates(cursor):
    """Remove duplicates by keeping the entry with the highest id."""
    cursor.execute('''
        DELETE FROM nonprofit_board_members
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM nonprofit_board_members
            GROUP BY person_name, org_name, years_of_service
        )
    ''')
    print("Duplicates removed.")


def populate_nonprofit_board_members(cursor, conn):
    """Insert data ensuring no new duplicates are added and show progress."""
    cursor.execute('SELECT COUNT(*) FROM officers')
    total_rows = cursor.fetchone()[0]

    for start in range(0, total_rows, BATCH_SIZE):
        cursor.execute(f'''
            INSERT OR IGNORE INTO nonprofit_board_members (
                person_name, title, hours_per_week, org_name, years_of_service, 
                total_revenue, city, state, ein
            )
            SELECT
                UPPER(o.person_name),
                UPPER(o.title),
                (SELECT hours_per_week FROM officers o2 
                 WHERE UPPER(o2.person_name) = UPPER(o.person_name) 
                   AND UPPER(o2.org_name) = UPPER(o.org_name) 
                   AND o2.year = (SELECT MAX(year) 
                                  FROM officers 
                                  WHERE UPPER(person_name) = UPPER(o2.person_name) 
                                    AND UPPER(org_name) = UPPER(o2.org_name))) AS hours_per_week,
                UPPER(o.org_name),
                GROUP_CONCAT(DISTINCT CAST(o.year AS TEXT)) AS years_of_service,
                o.total_revenue,
                UPPER((SELECT city FROM officers o3 
                       WHERE UPPER(o3.person_name) = UPPER(o.person_name) 
                         AND UPPER(o3.org_name) = UPPER(o.org_name) 
                         AND o3.year = (SELECT MAX(year) 
                                        FROM officers 
                                        WHERE UPPER(person_name) = UPPER(o3.person_name) 
                                          AND UPPER(org_name) = UPPER(o3.org_name)))) AS city,
                UPPER((SELECT state FROM officers o4 
                       WHERE UPPER(o4.person_name) = UPPER(o.person_name) 
                         AND UPPER(o4.org_name) = UPPER(o.org_name) 
                         AND o4.year = (SELECT MAX(year) 
                                        FROM officers 
                                        WHERE UPPER(person_name) = UPPER(o4.person_name) 
                                          AND UPPER(org_name) = UPPER(o4.org_name)))) AS state,
                o.ein  -- Include EIN
            FROM officers o
            WHERE o.rowid BETWEEN {start} AND {start + BATCH_SIZE - 1}
            GROUP BY UPPER(o.person_name), UPPER(o.org_name), o.ein  -- Group by EIN as well
        ''')
        conn.commit()  # Commit after each batch to ensure changes are saved
        print(f"Data insertion in progress. Processed rows {start + 1} to {min(start + BATCH_SIZE, total_rows)}.")

    print(f"Data insertion complete. {total_rows} rows processed.")


if __name__ == "__main__":
    main()
