import platform
import subprocess
from wcwidth import wcswidth

from .logger import (
    COLOR_WHITE,
    COLOR_RESET,
)

def git(cmd: str, default: str) -> str:
    try:
        return subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return default

VERSION = git("git describe --tags --always", "dev")
BRANCH = git("git branch --show-current", "main")
COMMIT = git("git rev-parse --short HEAD", "unknown")

PINK = "\033[38;2;255;126;182m"
TITLE = "\033[1;38;2;255;214;234m"
SEP = "\033[90m│\033[0m"

SAKURA_GRADIENT = [
    "\033[1;38;2;248;187;217m",
    "\033[1;38;2;247;168;207m",
    "\033[1;38;2;246;154;200m",
    "\033[1;38;2;245;140;193m",
    "\033[1;38;2;244;126;186m",
    "\033[1;38;2;243;112;179m",
    "\033[1;38;2;242;98;172m",
    "\033[1;38;2;241;84;165m",
    "\033[1;38;2;239;70;158m",
    "\033[1;38;2;237;56;151m",
    "\033[1;38;2;235;42;144m",
    "\033[1;38;2;233;28;137m",
    "\033[1;38;2;231;14;130m",
    "\033[1;38;2;229;0;123m",
    "\033[1;38;2;215;0;116m",
    "\033[1;38;2;201;0;109m",
    "\033[1;38;2;187;0;102m",
]

ASCII_LINES = [
    "⠀⠀⠀⠀⣀⡀",
    "⠀⠀⠀⠀⣿⠙⣦⠀⠀⠀⠀⠀⠀⣀⣤⡶⠛⠁",
    "⠀⠀⠀⠀⢻⠀⠈⠳⠀⠀⣀⣴⡾⠛⠁⣠⠂⢠⠇",
    "⠀⠀⠀⠀⠈⢀⣀⠤⢤⡶⠟⠁⢀⣴⣟⠀⠀⣾",
    "⠀⠀⠀⠠⠞⠉⢁⠀⠉⠀⢀⣠⣾⣿⣏⠀⢠⡇",
    "⠀⠀⡰⠋⠀⢰⠃⠀⠀⠉⠛⠿⠿⠏⠁⠀⣸⠁",
    "⠀⠀⣄⠀⠀⠏⣤⣤⣀⡀⠀⠀⠀⠀⠀⠾⢯⣀",
    "⠀⠀⣻⠃⠀⣰⡿⠛⠁⠀⠀⠀⢤⣀⡀⠀⠺⣿⡟⠛⠁",
    "⠀⡠⠋⡤⠠⠋⠀⠀⢀⠐⠁⠀⠈⣙⢯⡃⠀⢈⡻⣦",
    "⢰⣷⠇⠀⠀⠀⢀⡠⠃⠀⠀⠀⠀⠈⠻⢯⡄⠀⢻⣿⣷",
    "⠀⠉⠲⣶⣶⢾⣉⣐⡚⠋⠀⠀⠀⠀⠀⠘⠀⠀⡎⣿⣿⡇",
    "⠀⠀⠀⠀⠀⣸⣿⣿⣿⣷⡄⠀⠀⢠⣿⣴⠀⠀⣿⣿⣿⣧",
    "⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⠇⠀⢠⠟⣿⠏⢀⣾⠟⢸⣿⡇",
    "⠀⠀⢠⣿⣿⣿⣿⠟⠘⠁⢠⠜⢉⣐⡥⠞⠋⢁⣴⣿⣿⠃",
    "⠀⠀⣾⢻⣿⣿⠃⠀⠀⡀⢀⡄⠁⠀⠀⢠⡾⠁",
    "⠀⠀⠃⢸⣿⡇⠀⢠⣾⡇⢸⡇⠀⠀⠀⡞",
    "⠀⠀⠀⠈⢿⡇⡰⠋⠈⠙⠂⠙⠢",
    "⠀⠀⠀⠀⠈⢧",
]


def pad_display(text: str, width: int) -> str:
    return text + " " * max(0, width - wcswidth(text))

def print_banner() -> None:
    ascii_width = max(wcswidth(line) for line in ASCII_LINES)
    LABEL_WIDTH = 10
    right_info = {
        4: f"{COLOR_WHITE}HCaptcha Dataset Scraper{COLOR_RESET}",
        7: (
            f"{PINK}● {TITLE}{'Version':<{LABEL_WIDTH}}"
            f"{SEP} {COLOR_WHITE}{VERSION}{COLOR_RESET}"
        ),
        8: (
            f"{PINK}● {TITLE}{'Output':<{LABEL_WIDTH}}"
            f"{SEP} {COLOR_WHITE}./challenges{COLOR_RESET}"
        ),
        9: (
            f"{PINK}● {TITLE}{'Python':<{LABEL_WIDTH}}"
            f"{SEP} {COLOR_WHITE}{platform.python_version()}{COLOR_RESET}"
        ),
        10: (
            f"{PINK}● {TITLE}{'Platform':<{LABEL_WIDTH}}"
            f"{SEP} {COLOR_WHITE}{platform.system()}{COLOR_RESET}"
        ),
    }

    for i, line in enumerate(ASCII_LINES):
        color = SAKURA_GRADIENT[i % len(SAKURA_GRADIENT)]
        left = (
            f"{color}"
            f"{pad_display(line, ascii_width)}"
            f"{COLOR_RESET}"
        )
        print(f"{left}   {right_info.get(i, '')}")
    print()