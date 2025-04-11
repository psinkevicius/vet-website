import sqlite3
import json
import csv
import os
from datetime import datetime, timedelta

# Database and file paths
DB_PATH = 'instance/database.db'  # Ensure this path is correct for your SQLite database
ARCHIVE_DIR = 'Archive/'  # Directory where files will be stored
ARCHIVE_FORMAT = 'json'   # Change to 'csv' if you prefer CSV format

# Create archive directory if it doesn't exist
if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)


archive_threshold = (datetime.now() - timedelta(days=365)).date()  # Archive records older than one year

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# Step 1: Select records to archive
def fetch_records_to_archive():
    print(f"Archive threshold: {archive_threshold}")  # Debug print

    query = """
    SELECT * FROM uzsakymas
    WHERE (status = 'Completed' OR status = 'Cancelled') 
    AND DATE(date) < ?
    """
    cursor.execute(query, (archive_threshold,))
    records = cursor.fetchall()
    columns = [description[0] for description in cursor.description]

    print(f"Records fetched with date filter: {records}")  # Debug print
    return records, columns

# Step 2: Export records to file
def export_to_file(records, columns):
    if not records:
        print("No records to archive.")
        return None

    # Set the filename with a fixed base name 'archives' and a timestamp
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f"{ARCHIVE_DIR}archives_{timestamp}.{ARCHIVE_FORMAT}"

    if ARCHIVE_FORMAT == 'json':
        # Export to JSON
        with open(filename, 'w') as f:
            json_records = [dict(zip(columns, record)) for record in records]
            json.dump(json_records, f, indent=4, default=str)
    elif ARCHIVE_FORMAT == 'csv':
        # Export to CSV
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(columns)  # Write headers
            writer.writerows(records)
    else:
        raise ValueError("Unsupported archive format. Choose 'json' or 'csv'.")

    print(f"Archived {len(records)} records to {filename}")
    return filename

# Step 3: Delete archived records from database
def delete_archived_records(records):
    if not records:
        return

    ids_to_delete = [record[0] for record in records]  # Assumes first column is 'id'
    query = f"DELETE FROM uzsakymas WHERE id IN ({','.join(['?']*len(ids_to_delete))})"
    cursor.execute(query, ids_to_delete)
    conn.commit()
    print(f"Deleted {len(ids_to_delete)} archived records from the database.")

# Run the archiving process
def archive_old_appointments():
    records, columns = fetch_records_to_archive()
    if records:
        export_to_file(records, columns)
        delete_archived_records(records)
    else:
        print("No records met the archive criteria.")

# Call the archiving function
archive_old_appointments()

# Close the database connection
conn.close()
