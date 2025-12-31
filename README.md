# Bookie
A telegram bot to manage a local book club.

### PRE-REQUIREMENTS:
- Make sure you have a Telegram bot created with BotFather. Otherwise you won't have an API key.
## Quick install after cloning repo


```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
This will install the dependencies and setup a virtual env. 

**To run simply do: `python3 main.py`**

Replace config.py with your telegram user id and create a file called `token` with your Telegram API token

## List of Commands
```
/help - See how to the commands work
/add - Add a new book to reading list 
/list - Get books available from reading-list 
/log - Log your progress. e.g: /log 50 
/set - Set active book, e.g: /set YOUR_BOOK_TITLE 
/showlogs - Show your progress logs in table format 
/finish - Finish current active book
/leaderboard - See leaderboard on current active reading list 
```
