import sqlite3
import os

db_path = "beauty_index.db"
name_to_delete = "河北彩伽"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 文字列の完全一致と部分一致の両方で削除を試みる
    cursor.execute("DELETE FROM scores WHERE name = ?", (name_to_delete,))
    count1 = cursor.rowcount
    cursor.execute("DELETE FROM scores WHERE name LIKE ?", (f"%{name_to_delete}%",))
    count2 = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"Deleted {count1 + count2} records for {name_to_delete}.")
else:
    print("Database not found.")
