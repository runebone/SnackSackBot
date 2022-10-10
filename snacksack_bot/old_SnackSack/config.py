import os
import logging

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
PAYMENT_TOKEN = str(os.getenv("PAYMENT_TOKEN"))

DB_USER = str(os.getenv("DB_USER"))
DB_PASS = str(os.getenv("DB_PASS"))
DB_HOST = str(os.getenv("DB_HOST"))
DB_PORT = str(os.getenv("DB_PORT"))
DB_NAME = str(os.getenv("DB_NAME"))

bot_log_level = logging.DEBUG
bot_log_file = "bot.log"

db_log_level = logging.DEBUG
db_log_file = "database.log"
