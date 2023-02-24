# File with code for the telegram bot
CLEANUP_INTERVAL = 60*60

# Importing libraries
import logging, dotenv, os, sys, threading, time
import redis

from aiogram import Bot, Dispatcher, executor, types
import json
from typing import cast

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
# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher

bot = Bot(token=telegram_token)

dp = Dispatcher(bot)

# Ready to describe the endpoints

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    user_info = get_user_info(message)
    database_user_key = f"user_{user_info['user_id']}"
    if not redis_tools.check_if_user_exists(redis_connection, database_user_key, redis_tools.ALL_USERS):
        redis_tools.add_user_to_group(redis_connection, database_user_key, redis_tools.ALL_USERS)

    logging.info(f"User with nickname {user_info['user_username']} started the bot.")
    await message.reply(msgs.welcome_msg)
    await message.reply(msgs.values)

@dp.message_handler(commands=['poll'])
async def send_poll(message):
    await message.reply(msgs.poll_msg, reply_markup=msgs.poll)

@dp.callback_query_handler()
async def callback_query(call):
    data = json.loads(call.data)
    chat_id = call['message']['chat']['id']
    message_id = call['message']['message_id']
    keyboard = call['message']['reply_markup']['inline_keyboard']
    selected = [
        json.loads(button[0]['callback_data']).get('selected', 0)
        for button in keyboard
    ]
    max_selected = max(selected)
    if data['type'] == 'answer':
        if max_selected >= 6:
            return
        key = data['key']
        new_button = keyboard[key][0]
        callback_data = json.loads(new_button['callback_data'])
        if callback_data['selected'] > 0:
            return
        new_button['text'] = f'({max_selected + 1})  ' + new_button['text']
        callback_data['selected'] = max_selected + 1
        new_button['callback_data'] = json.dumps(callback_data)
        keyboard[key][0] = new_button
        keyb_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=keyb_markup)
    elif data['type'] == 'clear':
        new_keyboard = []
        for button in keyboard:
            button[0]['text'] = button[0]['text'].split(') ')[-1]
            callback_data = json.loads(button[0]['callback_data'])
            if callback_data.get('selected', 0) > 0:
                callback_data['selected'] = 0
                button[0]['callback_data'] = json.dumps(callback_data)
            new_keyboard.append(button)
        keyb_markup = types.InlineKeyboardMarkup(inline_keyboard=new_keyboard)
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=keyb_markup)
    elif data['type'] == 'ok':
        result = [(key, val) for key, val in enumerate(selected) if val != 0]
        result.sort(key=lambda x: x[1])
        if max_selected < 6:
            return
        user_info = get_user_info(call['message'])
        database_user_key = f"user_{user_info['user_id']}"
        #redis_tools.save_polling_result(redis_connection, database_user_key, [val[0] for val in result])
        await bot.send_message(chat_id, msgs.after_poll_msg)

### ADD YOUR ENDPOINTS HERE ###

# Start the bot

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)