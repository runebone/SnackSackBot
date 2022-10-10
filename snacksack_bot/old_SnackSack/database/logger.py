import logging

from SnackSack.config import db_log_file
from SnackSack.config import db_log_level


logger = logging.getLogger(__name__)

logger.setLevel(db_log_level)

formatter = logging.Formatter("%(asctime)s (%(levelname)s) - %(message)s")

file_handler = logging.FileHandler(db_log_file)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
