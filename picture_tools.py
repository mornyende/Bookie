from rich.table import Table
from rich.console import Console
from rich.align import Align
from rich.terminal_theme import TerminalTheme

import cairosvg

import sqlite3
from datetime import *
from collections import defaultdict

GRUVBOX = TerminalTheme(

#    Args:
#        background (Tuple[int, int, int]): The background color.
#        foreground (Tuple[int, int, int]): The foreground (text) color.
#        normal (List[Tuple[int, int, int]]): A list of 8 normal intensity colors.
#        bright (List[Tuple[int, int, int]], optional): A list of 8 bright colors, or None
#            to repeat normal intensity. Defaults to None.

    (40, 40, 40),
    (253, 244, 193),
    [
        (60, 56, 54), #bg1
        (204, 36, 29), #red
        (152, 151, 26), #green
        (215, 153, 33), #yellow
        (69, 133, 136), #blue
        (177, 98, 134), #purple
        (104, 157, 106), #aqua
        (214, 93, 14), #orange
        (168, 153, 132), #gray
    ],
    [
        (244, 0, 95),
        (152, 224, 36),
        (224, 213, 97),
        (157, 101, 255),
        (244, 0, 95),
        (88, 209, 235),
        (246, 246, 239),
    ],
)

CONSOLE_SVG_FORMAT2 = """\
<svg class="rich-terminal" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <!-- Generated with Rich https://www.textualize.io -->
    <style>

    @font-face {{
        font-family: "Fira Code";
        src: local("FiraCodeNerdFont-Regular"),
                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Regular.woff2") format("woff2"),
                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff/FiraCode-Regular.woff") format("woff");
        font-style: normal;
        font-weight: 400;
    }}
    @font-face {{
        font-family: "Fira Code";
        src: local("FiraCodeNerdFont-Bold"),
                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Bold.woff2") format("woff2"),
                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff/FiraCode-Bold.woff") format("woff");
        font-style: bold;
        font-weight: 700;
    }}

    .{unique_id}-matrix {{
        font-family: FiraCode Nerd Font Mono, monospace;
        font-size: {char_height}px;
        line-height: {line_height}px;
        font-variant-east-asian: full-width;
    }}

    .{unique_id}-title {{
        font-size: 18px;
        font-weight: bold;
        font-family: arial;
    }}

    {styles}
    </style>

    <rect width="100%" height="100%" fill="#282828" />

    <defs>
    <clipPath id="{unique_id}-clip-terminal">
      <rect x="0" y="0" width="{terminal_width}" height="{terminal_height}" />
    </clipPath>
    {lines}
    </defs>

    
    <g transform="translate({terminal_x}, {terminal_y})" clip-path="url(#{unique_id}-clip-terminal)">
    {backgrounds}
    <g class="{unique_id}-matrix">
    {matrix}
    </g>
    </g>
</svg>
"""

def progress_table(data, colnames,title):
    table = Table(title=title)

    #table.add_column(colnames[0], justify="right", style="cyan", no_wrap=True)
    table.add_column(colnames[0], style="magenta")
    table.add_column(colnames[1], justify="right", style="green")

    for row in data:
        table.add_row(*row)

    console = Console(record=True,width=40)

    centered_table = Align.center(table)
    console.print(centered_table)

    svg_data = console.export_svg(theme=GRUVBOX,title="",clear=True, 
                                  code_format=CONSOLE_SVG_FORMAT2,font_aspect_ratio=0.60)

    cairosvg.svg2png(bytestring=svg_data.encode(), write_to="output.png",)

def this_years_readinglist(year):
    conn = sqlite3.connect("bookie.db")
    cursor = conn.cursor()

    if year =="":
        today = datetime.today().strftime("%V")
        thisyear = datetime.today().strftime("%Y")
        p = f"ㅤ      {thisyear}\n"
        i = 0
        reading_list = cursor.execute("SELECT title,start_date FROM BOOKS WHERE "\
                        f"start_date LIKE '{thisyear}%' ORDER BY start_date").fetchall()

        reading_list = booklist_helper(reading_list)

        for row in reading_list:
            if row[0]==today:
                p = p+"Week "+row[0]+" (*) "+row[1]+"\n"
                i+=1
            elif int(row[0])>int(today) and i==0:
                p = p+"Week "+today+" (*)\n"
                i+=1
                p = p+"Week "+row[0]+"  :  "+row[1]+"\n"
            else:
                p = p+"Week "+row[0]+"  :  "+row[1]+"\n"

        if i==0:
            p = p+"Week "+today+" (*)\n"

    else:
        p = f"ㅤ      {year}\n"
        reading_list = cursor.execute("SELECT title,start_date FROM BOOKS WHERE "\
                        f"start_date LIKE '{year}%' ORDER BY start_date").fetchall()
        reading_list = booklist_helper(reading_list)

        for row in reading_list:
            p = p+"Week "+row[0]+"  :  "+row[1]+"\n"

    return p


def booklist_helper(fetched_list):
    # 1. Simulate the output from cursor.fetchall()
    # Example data structure: List of (title, start_date) tuples

    # 2. Initialize a dictionary to group titles by week
    # Using defaultdict(list) makes it easy to append titles without checking if keys exist
    books_by_week = defaultdict(list)

    for title, date_str in fetched_list:
        # Convert string to datetime object (adjust format '%Y-%m-%d' if your DB differs)
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Get ISO week number (returns tuple: year, week, weekday)
        # Index [1] gives the week number
        week_num = dt.strftime("%V")
        
        books_by_week[week_num].append(title)

    # 3. Create the final list with pasted titles
    # Join titles with a separator (e.g., ", " or " & ")
    final_output = [
        (week, " ; ".join(titles)) 
        for week, titles in sorted(books_by_week.items())
    ]

    # Output: [(1, 'The Great Gatsby, 1984'), (3, 'Brave New World, The Hobbit')]
    return final_output

def leaderboard_table(data, title):
    table = Table(title=title, show_header=False)
    table.add_column("Username", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Progress (%)", justify="right", style="blue")

    for row in data:
        table.add_row(*[
            str(item)[:25] + "..." if len(str(item)) > 28 else str(item)
            for item in row
        ])    
    console = Console(record=True,width=60)

    centered_table = Align.center(table)
    console.print(centered_table)

    svg_data = console.export_svg(theme=GRUVBOX,title="",clear=True, 
                                  code_format=CONSOLE_SVG_FORMAT2,font_aspect_ratio=0.60)

    cairosvg.svg2png(bytestring=svg_data.encode(), write_to="leaderboard.png",)