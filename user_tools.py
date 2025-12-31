import sqlite3

def get_user_active_book(username: str) -> str : 
    conn = sqlite3.connect("bookie.db")
    conn.row_factory = lambda cursor, row: row[0]
    cursor = conn.cursor()
    result = cursor.execute(f'SELECT book_title FROM ACTIVE_BOOKS WHERE username="{username}" LIMIT 1').fetchone()

    return result