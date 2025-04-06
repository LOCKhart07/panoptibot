import logging


def set_logging():
    """Set logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    OTHER_LOGGERS = [
        "httpx",
        "apscheduler.scheduler",
        "apscheduler.executors",
        "apscheduler.executors.default",
        "telegram.ext.Application",
    ]

    # Lower other loggers logging level to reduce log pollution
    for logger_name in OTHER_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.ERROR)


def format_table(data):
    """Format a table from a list of lists"""
    col_widths = [max(len(str(item)) for item in col) for col in zip(*data)]

    lines = [
        " ".join(str(item).ljust(width) for item, width in zip(row, col_widths))
        for row in data
    ]

    return "\n".join(lines)
