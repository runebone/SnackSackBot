import logging

from SnackSack.config import bot_log_file
from SnackSack.config import bot_log_level


logger = logging.getLogger(__name__)

logger.setLevel(bot_log_level)

formatter = logging.Formatter("%(asctime)s (%(levelname)s) - %(message)s")

file_handler = logging.FileHandler(bot_log_file)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
