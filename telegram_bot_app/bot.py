# File with code for the telegram bot
CLEANUP_INTERVAL = 60*60

# Importing libraries
import logging, dotenv, os, sys, threading, time
import redis
import telebot


# Local imports
import msgs
import redis_tools

# Logging
import logging.handlers
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


# Importing settings and environment variables

script_dir_full = os.path.dirname(os.path.realpath(__file__))
try:
    dotenv.load_dotenv(os.path.join(script_dir_full, ".." ,'.env'))
    logging.info("Loaded .env file")
except Exception as e:
    logging.error("Error loading .env file: ", e)
    sys.exit(1)

# Redis database
redis_hosts = os.getenv("REDIS_HOSTS").split(",")
redis_port = os.getenv("REDIS_PORT")

# Connecting to redis
connected_to_redis = False
for host in redis_hosts:
    connection = redis.Redis(
    host=host,
    port=redis_port,
    )
    try:
        if connection.ping():
            logging.info(f"Connected to redis host {host}")
            connected_to_redis = True
            redis_connection = connection
            break
    except Exception as e:
        logging.error(f"Could not connect to redis host {host}: {e}")
if not connected_to_redis:
    logging.error("Could not connect to redis")
    sys.exit(1)


def get_user_info(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    last_name = message.from_user.last_name
    user_username = message.from_user.username
    user_info = {
        "user_id": user_id,
        "user_name": user_name,
        "user_username": user_username,
        "user_last_name": last_name
    }
    return user_info

# Writing bot

# Telegram bot
telegram_token = os.getenv("TELEGRAM_API_KEY")
logger = telebot.logger
telebot.logger.setLevel(logging.WARNING) # Outputs debug messages to console.

bot = telebot.TeleBot(telegram_token, parse_mode=None) # You can set parse_mode by default. HTML or MARKDOWN


# Ready to describe the endpoints

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_info = get_user_info(message)
    database_user_key = f"user_{user_info['user_id']}"
    if not redis_tools.check_if_user_exists(redis_connection, database_user_key, redis_tools.ALL_USERS):
        redis_tools.add_user_to_group(redis_connection, database_user_key, redis_tools.ALL_USERS)
    logging.info(f"User with nickname {user_info['user_username']} started the bot.")
    bot.reply_to(message, msgs.welcome_msg)

    

### ADD YOUR ENDPOINTS HERE ###
    
    
# Start the bot
bot.infinity_polling()