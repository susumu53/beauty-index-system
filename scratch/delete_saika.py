import sqlite3
import os

db_path = "beauty_index.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT name FROM scores WHERE name LIKE '%河北彩伽%'")
    rows = cursor.fetchall()
    if rows:
        print(f"Found entries to delete: {rows}")
        cursor.execute("DELETE FROM scores WHERE name LIKE '%河北彩伽%'")
        conn.commit()
        print("Deleted.")
    else:
        print("No entries found for 河北彩伽.")
    
    conn.close()
else:
    print(f"Database {db_path} not found.")
