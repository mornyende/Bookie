# your telegram token in a togen file
with open('togen') as f: togen = f.read()
import logging
import sqlite3
from datetime import datetime

from math import floor

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from book_tools import *
from user_tools import *
from picture_tools import *
from config import *


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def initDb():
    conn = sqlite3.connect("bookie.db")
    conn.execute("CREATE TABLE IF NOT EXISTS BOOKS(title, author, year, page_count, start_date, end_date)")
    conn.execute("CREATE TABLE IF NOT EXISTS PROGRESS(username, title, date, prog_perc)")
    conn.execute("CREATE TABLE IF NOT EXISTS ACTIVE_BOOKS(username, book_title)")

def initHandlers(application: Application):
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("list", get_reading_list))
    application.add_handler(CommandHandler("log", log))
    application.add_handler(CommandHandler("log2", log2))
    application.add_handler(CommandHandler("set", set_active_book))
    application.add_handler(CommandHandler("finish", finish))
    application.add_handler(CommandHandler("showlogs", show_logs))
    application.add_handler(CommandHandler("leaderboard", show_current_progress))
    application.add_handler(CommandHandler("club_leaderboard",show_current_book_leaderboard))
    application.add_handler(CommandHandler("drop", drop_active_book))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help = (
        "/help - See how to the commands work \n"
        "/add - Add a new book to reading list \n"
        "/list - Get books available from reading-list \n"
        "/log - Log your progress. e.g: /log 50 \n"
        "/set - Set active book, e.g: /set YOUR_BOOK_TITLE \n"
        "/showlogs - Show your progress logs in table format \n"
        "/finish - Finish current active book\n"
        "/leaderboard - See leaderboard on current active reading list \n"
    )
    await update.message.reply_text(help)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adds a new book to the BOOKS table"""
    if update.effective_user.id not in god:
        return
    conn = sqlite3.connect("bookie.db")
    try:
        book = update.message.text[5:]
        book = list(map(str.strip, book.split(',')))

        if len(book) < 3 or len(book) == 5:
            await update.message.reply_text("Invalid input :3c")
            return

        if len(book) == 4:
            conn.execute(
                "INSERT INTO BOOKS VALUES (?, ?, ?, ?, NULL, NULL)",
                (book[0], book[1], int(book[2]), int(book[3]))
            )

        elif len(book) == 3:
            conn.execute(
                "INSERT INTO BOOKS VALUES (?, ?, ?, NULL, NULL, NULL)",
                (book[0], book[1], int(book[2]))
            )

        else:
            conn.execute(
                "INSERT INTO BOOKS VALUES (?, ?, ?, ?, ?, ?)",
                (book[0], book[1], int(book[2]), int(book[3]), book[4], book[5])
            )

        conn.commit()
        await update.message.reply_text(f"{book[0]} ({book[2]}) by {book[1]} added to the reading list :3")
    except Exception as e:
        print(e)
        await update.message.reply_text(f"Failed to add book to reading list. Try again please.")
        return;

async def get_reading_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Outputs the reading list ordered by date"""
    try:
        year = update.message.text[6:]
        message = this_years_readinglist(year)
        await update.message.reply_text(message)
    except Exception as e:
        print(e)
        await update.message.reply_text("Failed to fetch reading list. Try again later")
        return


async def get_recent_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Outputs the books set to be read this month, prev month, and next month"""
    await update.message.reply_text(get_recent_book_titles().join('\\n'))


async def set_active_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the active book for the user, argument order: title"""
    user = update.effective_user.username or update.effective_user.first_name
    try:
        title = update.message.text[5:]
        books = search_book_titles(title)

        if len(books) == 0:
            await update.message.reply_text(f"404: Book not found")
            return
        if len(books) > 1:
            book_list = '\n'.join(b for b in books)
            await update.message.reply_text(
                f"Found {len(books)} books:\n{book_list}\nRe-Run the /set command with the appropriate title."
            )
            return

        conn = sqlite3.connect("bookie.db")

        conn.execute("DELETE FROM ACTIVE_BOOKS WHERE username = ?", (user,))
        conn.execute("INSERT INTO ACTIVE_BOOKS (username, book_title) VALUES (?, ?)", (user, books[0]))
        conn.commit()
    except Exception as e:
        print(e)
        await update.message.reply_text(f"Failed to set active book. Try again please.")
        return
    await update.message.reply_text(f"{user} is now reading {title}!")

async def drop_active_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Drops active book"""
    conn = sqlite3.connect("bookie.db")
    user = update.effective_user.username or update.effective_user.first_name

    try:
        conn.execute("DELETE FROM ACTIVE_BOOKS WHERE username = ?", (user,))
        conn.commit()
    except Exception as e:
        print(e)
        await update.message.reply_text(f"Couldn't delete active book.. oopsie!!")
        return

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs a user's reading progress, name + date + amount"""
    conn = sqlite3.connect("bookie.db")
    conn.row_factory = lambda cursor, row: row[0]
    cursor = conn.cursor()
    try:
        user = update.effective_user.username
        first_name = update.effective_user.first_name
        user = user or first_name
        active_book = get_user_active_book(user)

        if (active_book is None):
            await update.message.reply_text("You do not have any active books currently. Run /set <book title>")
            return

        # Order of input (date, % or two numbers)
        log = update.message.text[5:]
        log = list(map(str.strip, log.split(',')))

        if len(log) >3 or len(log) == 0:
            await update.message.reply_text("Invalid input :3c")
            return
        
        if any(" " in s for s in log):
            await update.message.reply_text("Did you forget to use commas?")
            return

        if '-' in log[0]:
            date = log[0]
            if len(log)==2:
                perc = int(log[1])
            else:
                perc = floor(100*int(log[1])/int(log[2]))
        else:
            date = datetime.today().strftime("%Y-%m-%d")
            if len(log)==1:
                perc = int(log[0])
            else:
                perc = floor(100*int(log[0])/int(log[1]))

        previous_log = cursor.execute(
            "SELECT prog_perc FROM PROGRESS WHERE username = ? AND title = ? AND date = ? LIMIT 1",
            (user, active_book, date)
        ).fetchall()
        
        if len(previous_log)>0 and previous_log[0]==100:
            await update.message.reply_text(f"You've finished the book - /set a new book first")
            return
        elif len(previous_log)>0 and perc<previous_log[0]:
            await update.message.reply_text(f"You already had more progress ({previous_log[0]}%) logged for {date}")
            return
        elif len(previous_log)>0:
            await update.message.reply_text(f"Updating {date} log from {previous_log[0]}% to {perc}%")

            conn.execute(
                "UPDATE PROGRESS SET prog_perc = ? WHERE username = ? AND title = ? AND date = ?",
                (perc, user, active_book, date)
            )
            conn.commit()
            return

        conn.execute("INSERT INTO PROGRESS VALUES (?,?,?,?)",
                    (user, active_book, date, perc))
        conn.commit()
    except Exception as e:
        print(e)
        await update.message.reply_text(f"Failed to log progress. Try again please.")
        return
    await update.message.reply_text(f"{user} is {perc}% through {active_book}!")

async def log2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs a user's reading progress, name + date + amount"""
    conn = sqlite3.connect("bookie.db")
    conn.row_factory = lambda cursor, row: row[0]
    cursor = conn.cursor()
    try:
        user = update.effective_user.username
        first_name = update.effective_user.first_name
        user = user or first_name
        
        # Order of input (date, % or two numbers)
        log = update.message.text[6:]
        log = list(map(str.strip, log.split(',')))
        
        active_book = log[0]

        if len(log) >4 or len(log) == 0:
            await update.message.reply_text("Invalid input :3c")
            return

        if '-' in log[1]:
            date = log[1]
            if len(log)==3:
                perc = int(log[2])
            else:
                perc = floor(100*int(log[2])/int(log[3]))
        else:
            date = datetime.today().strftime("%Y-%m-%d")
            if len(log)==2:
                perc = int(log[1])
            else:
                perc = floor(100*int(log[1])/int(log[2]))

        previous_log = cursor.execute(
            "SELECT prog_perc FROM PROGRESS WHERE username = ? AND title = ? AND date = ? LIMIT 1",
            (user, active_book, date)
        ).fetchall()
                
        if len(previous_log)>0 and perc<previous_log[0]:
            await update.message.reply_text(f"You already had more progress ({previous_log[0]}%) logged for {date}")
            return
        if len(previous_log)>0:
            await update.message.reply_text(f"Updating {date} log from {previous_log[0]}% to {perc}%")

            conn.execute(
                "UPDATE PROGRESS SET prog_perc = ? WHERE username = ? AND title = ? AND date = ?",
                (perc, user, active_book, date)
            )
            conn.commit()
            return

        conn.execute("INSERT INTO PROGRESS VALUES (?,?,?,?)",
                    (user, active_book, date, perc))
        conn.commit()
    except Exception as e:
        print(e)
        await update.message.reply_text(f"Failed to log progress. Try again please.")
        return
    await update.message.reply_text(f"{user} is {perc}% through {active_book}!")


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect("bookie.db")
    user = update.effective_user.username or update.effective_user.first_name
    try:
        active_book = get_user_active_book(user)

        date = update.message.text[8:]
        if '-' in date:
            conn.execute("INSERT INTO PROGRESS VALUES (?,?,?,?)",
                    (user, active_book, date, 100))
        else:
            conn.execute("INSERT INTO PROGRESS VALUES (?,?,?,?)",
                    (user, active_book, datetime.today().strftime("%Y-%m-%d"), 100))
        
        conn.commit()
    except Exception as e:
        print(e)
        await update.message.reply_text("Failed to mark book as finished, try again :(")
        return
    await update.message.reply_text(f"{user} has finished {active_book}! Yippee")


async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user.username or update.effective_user.first_name
    conn = sqlite3.connect("bookie.db")
    try:
        conn.row_factory = lambda cursor, row: [str(val) if val is not None else '' for val in row]
        cursor = conn.cursor()

        active_book = get_user_active_book(user)

        if active_book == None:
            await update.message.reply_text(f"You don't have an active book set!!!")
            return

        logs = cursor.execute(
            "SELECT date, prog_perc FROM PROGRESS WHERE username = ? AND title = ?",
            (user, active_book)
        ).fetchall()
        
        progress_table([(x, y + "%") for x, y in logs],
                ["Date","Progress"],f"{user}'s progress on {active_book}")
        await update.message.reply_photo(photo=open('output.png', 'rb'),
            caption=f"{user}'s progress on {active_book} on {datetime.today().strftime("%Y-%m-%d")}")
    except Exception as e:
        print(e)
        await update.message.reply_text(f"Failed to show {user} logs. Try again please.")
        return

async def show_current_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect("bookie.db")
    cursor = conn.cursor()

    try:
        list = cursor.execute("""SELECT
            a.username,
            a.book_title,
            COALESCE(MAX(b.prog_perc),0) AS prog_perc
        FROM ACTIVE_BOOKS a
        LEFT JOIN PROGRESS b
            ON a.username = b.username
        AND a.book_title = b.title
        GROUP BY
            a.username,
            a.book_title
        ORDER BY
            prog_perc DESC;""").fetchall()
        
        leaderboard_table(list, "Leaderboard")
        await update.message.reply_photo(photo=open('leaderboard.png', 'rb'),
        caption=f"Leaderboard on {datetime.today().strftime("%Y-%m-%d")}")
    except Exception as e:
        print(e)
        await update.message.reply_text("Failed to show leaderboard. Try again please.")

async def show_current_book_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect("bookie.db")
    cursor = conn.cursor()
    date = datetime.today().strftime("%Y-%m-%d")

    try:
        list = cursor.execute(f"""SELECT
            b.username,
            a.title,
            COALESCE(MAX(b.prog_perc),0) AS prog_perc
        FROM BOOKS a
        LEFT JOIN PROGRESS b
        ON a.title = b.title
        WHERE a.start_date<='{date}' AND a.end_date>='{date}'
        GROUP BY
            b.username,
            a.title
        ORDER BY
            prog_perc DESC;""").fetchall()
        
        leaderboard_table(list, "Based Poets Society update")
        await update.message.reply_photo(photo=open('leaderboard.png', 'rb'),
        caption=f"Communal reading progress on {datetime.today().strftime("%Y-%m-%d")}")
    except Exception as e:
        print(e)
        await update.message.reply_text("Failed to show leaderboard. Try again please.")

def main() -> None:
    """Start the bot."""
    """Initialize DB with specific tables"""
    initDb()
    application = Application.builder().token(togen).build()
    initHandlers(application)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    
if __name__ == "__main__":
    main()