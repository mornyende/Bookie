import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_all_book_titles() -> list[str]:
    conn = sqlite3.connect("bookie.db")
    conn.row_factory = lambda cursor, row: row[0]

    cursor = conn.cursor()
    book_titles = cursor.execute(f"SELECT title FROM BOOKS").fetchall()
    return book_titles

def search_book_titles(query: str) -> list[str]:
    conn = sqlite3.connect("bookie.db")
    conn.row_factory = lambda cursor, row: row[0]

    cursor = conn.cursor()
    book_titles = cursor.execute(
        "SELECT title FROM BOOKS WHERE title LIKE ?",
        (f"%{query}%",)).fetchall()
    return book_titles
    
def get_recent_book_titles() -> list[str]:
    this_month = datetime.today().strftime('%Y-%m')
    prev_month = (datetime.today()-relativedelta(months=1)).strftime('%Y-%m')
    next_month = (datetime.today()+relativedelta(months=1)).strftime('%Y-%m')

    conn = sqlite3.connect("bookie.db")
    conn.row_factory = lambda cursor, row: row[0]

    cursor = conn.cursor()
    book_titles = cursor.execute(f"SELECT title FROM BOOKS WHERE start_date LIKE '{prev_month}%'"\
                                f" OR start_date LIKE '{this_month}%'" \
                                f" OR start_date LIKE '{next_month}%'").fetchall()
    return book_titles

def get_current_club_book_titles(date=datetime.today().strftime('%Y-%m-%d')) -> list[str]:
    conn = sqlite3.connect("bookie.db")
    conn.row_factory = lambda cursor, row: row[0]

    cursor = conn.cursor()
    book_titles = cursor.execute(f"SELECT title FROM BOOKS WHERE start_date <= '{date}%'"\
                                f" AND end_date >= '{date}%'").fetchall()
    print(date)
    return book_titles


