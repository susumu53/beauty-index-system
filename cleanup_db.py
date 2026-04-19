import sqlite3

def cleanup_database():
    conn = sqlite3.connect('beauty_index.db')
    cursor = conn.cursor()
    
    # 1. 重複している名前とカテゴリのリストを取得
    cursor.execute("SELECT name, category FROM scores GROUP BY name, category HAVING COUNT(*) > 1")
    duplicates = cursor.fetchall()
    
    for name, category in duplicates:
        print(f"Cleaning up duplicates for: {name} ({category})")
        # 最も高いスコアのID（同点の場合は最新）を取得
        cursor.execute("""
            SELECT id FROM scores 
            WHERE name = ? AND category = ? 
            ORDER BY total_score DESC, created_at DESC 
            LIMIT 1
        """, (name, category))
        best_id = cursor.fetchone()[0]
        
        # それ以外のIDをすべて削除
        cursor.execute("""
            DELETE FROM scores 
            WHERE name = ? AND category = ? AND id != ?
        """, (name, category, best_id))
    
    conn.commit()
    conn.close()
    print("Cleanup complete.")

if __name__ == "__main__":
    cleanup_database()
