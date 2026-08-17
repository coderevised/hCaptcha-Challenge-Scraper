import logging

COLOR_RESET = "\033[0m"
COLOR_DIM = "\033[90m"

COLOR_BLUE = "\033[38;2;74;163;255m"
COLOR_GREEN = "\033[38;2;0;255;0m"
COLOR_BRIGHT_GREEN = "\033[38;2;0;255;127m"
COLOR_YELLOW = "\033[38;2;255;179;0m"
COLOR_RED = "\033[38;2;211;47;47m"
COLOR_MAGENTA = "\033[38;2;156;39;176m"
COLOR_CYAN = "\033[38;2;0;255;255m"
COLOR_GRAY = "\033[38;2;128;128;128m"
COLOR_WHITE = "\033[97m"

OK_LEVEL_NUM = 25
SAVE_LEVEL_NUM = 26
logging.addLevelName(OK_LEVEL_NUM, "OK")
logging.addLevelName(SAVE_LEVEL_NUM, "SAVE")

LEVEL_COLORS = {
    "INFO": COLOR_BLUE,
    "OK": COLOR_GREEN,
    "SAVE": COLOR_BRIGHT_GREEN,
    "WARNING": COLOR_YELLOW,
    "ERROR": COLOR_RED,
}

COMPONENT_COLORS = {
    "Config": COLOR_GRAY,
    "Session": COLOR_CYAN,
    "Collector": COLOR_BLUE,
    "Solver": COLOR_MAGENTA,
    "Network": COLOR_YELLOW,
    "Saver": COLOR_GREEN,
    "Storage": COLOR_BRIGHT_GREEN,
    "Summary": COLOR_WHITE,
}


class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = self.formatTime(record, "%H:%M:%S")
        ts_colored = f"{COLOR_DIM}{ts}{COLOR_RESET}"
        level_plain = record.levelname.ljust(9)
        level_color = LEVEL_COLORS.get(record.levelname, COLOR_RESET)
        level_colored = f"{level_color}{level_plain}{COLOR_RESET}"
        comp = getattr(record, "component", "GENERAL")
        comp_color = COMPONENT_COLORS.get(comp, COLOR_RESET)
        comp_plain = comp.ljust(14)
        comp_colored = f"{comp_color}{comp_plain}{COLOR_RESET}"
        msg = record.getMessage()
        return f"{ts_colored} {level_colored} {comp_colored} {msg}"


class ComponentAdapter(logging.LoggerAdapter):
    def __init__(self, logger: logging.Logger, component: str):
        super().__init__(logger, {"component": component})

    def ok(self, msg: str, *args, **kwargs) -> None:
        self.log(OK_LEVEL_NUM, msg, *args, **kwargs)

    def save(self, msg: str, *args, **kwargs) -> None:
        self.log(SAVE_LEVEL_NUM, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.log(logging.ERROR, msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        self.log(logging.ERROR, msg, *args, exc_info=True, **kwargs)


def get_logger(component: str) -> ComponentAdapter:
    logger = logging.getLogger("hcaptcha_scraper")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(CustomFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return ComponentAdapter(logger, component)