# Copyright (©) 2025, Alexander Suvorov. All rights reserved.
import os
from typing import List

class Colors:
    HEADER = '\033[95m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_RED = '\033[41m'


class Icons:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "💡"
    SYNC = "🔄"
    USER = "👤"
    REPO = "📁"
    KEY = "🔑"
    GITHUB = "🐙"
    SSH = "🔐"
    EXIT = "🚪"
    BACK = "↩️"
    REFRESH = "🔃"
    SEARCH = "🔍"
    DELETE = "🗑️"
    STORAGE = "💾"
    SETTINGS = "⚙️"
    FOLDER = "📂"
    CLOUD = "☁️"
    LOCK = "🔒"
    UNLOCK = "🔓"
    QUESTION = "❓"
    CHECK = "✓"
    CROSS = "✗"
    STATS = "📊"
    LANGUAGE = "💻"
    STAR = "⭐"
    FORK = "🍴"
    CALENDAR = "📅"
    CLOCK = "⏰"
    DOWNLOAD = "📥"
    UPLOAD = "📤"
    NETWORK = "🌐"
    HOME = "🏠"
    LIST = "📋"
    FILTER = "🔍"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_section(title: str, width: int = 60):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * width}")
    print(f"{title.center(width)}")
    print(f"{'=' * width}{Colors.END}")


def print_subsection(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {title}{Colors.END}")


def print_success(text: str, icon: str = Icons.SUCCESS):
    print(f"{Colors.GREEN}{icon} {text}{Colors.END}")


def print_error(text: str, icon: str = Icons.ERROR):
    print(f"{Colors.RED}{icon} {text}{Colors.END}")


def print_warning(text: str, icon: str = Icons.WARNING):
    print(f"{Colors.YELLOW}{icon} {text}{Colors.END}")


def print_info(text: str, icon: str = Icons.INFO):
    print(f"{Colors.CYAN}{icon} {text}{Colors.END}")


def print_menu_item(number: str, text: str, icon: str = ""):
    if icon:
        print(f"  {Colors.BOLD}{Colors.BLUE}{number}.{Colors.END} {icon} {text}")
    else:
        print(f"  {Colors.BOLD}{Colors.BLUE}{number}.{Colors.END} {text}")


def print_table(headers: List[str], rows: List[List], max_width: int = 60):
    if not rows:
        print_info("No data to display")
        return

    col_widths = []
    for i in range(len(headers)):
        max_len = len(str(headers[i]))
        for row in rows:
            if i < len(row):
                max_len = max(max_len, len(str(row[i])))
        col_widths.append(min(max_len, max_width))

    header_line = " | ".join(
        f"{Colors.BOLD}{str(h).ljust(col_widths[i])[:max_width]}{Colors.END}"
        for i, h in enumerate(headers)
    )
    print(f"\n{header_line}")
    print("-+-".join("-" * width for width in col_widths))

    for row in rows:
        display_row = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                cell_str = str(cell)
                if len(cell_str) > max_width:
                    cell_str = cell_str[:max_width - 3] + "..."
                display_row.append(cell_str.ljust(col_widths[i])[:max_width])
        print(" | ".join(display_row))


def print_progress_bar(iteration: int, total: int, prefix: str = '', suffix: str = '',
                       length: int = 40, fill: str = '█'):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total:
        print()


def wait_for_enter(prompt: str = "Press Enter to continue..."):
    print(f"\n{Colors.YELLOW}{prompt}{Colors.END}", end="")
    input()
