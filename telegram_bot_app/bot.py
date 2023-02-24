# File with code for the telegram bot
CLEANUP_INTERVAL = 60*60

# Importing libraries
import logging, dotenv, os, sys, threading, time
import redis

from aiogram import Bot, Dispatcher, executor, types
import json

# Local imports
import msgs
import redis_tools
import magic

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
logging.basicConfig(level=logging.WARNING)

# Initialize bot and dispatcher

bot = Bot(token=telegram_token)

dp = Dispatcher(bot)

# Ready to describe the endpoints

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    user_info = get_user_info(message)
    chat_id = message.chat.id
    database_user_key = f"{user_info['user_username']}".strip()
    if not redis_tools.check_if_user_exists(redis_connection, database_user_key, redis_tools.ALL_USERS):
        redis_tools.add_user_to_group(redis_connection, database_user_key, redis_tools.ALL_USERS)
        redis_tools.save_user_chat_id(redis_connection, database_user_key, chat_id)
    logging.info(f"User with nickname {user_info['user_username']} started the bot.")
    await message.reply(msgs.welcome_msg)
    await message.reply(msgs.values, reply_markup=msgs.go_next_btn(0))


@dp.callback_query_handler()
async def callback_query(call):
    data = json.loads(call.data)
    chat_id = call['message']['chat']['id']
    message_id = call['message']['message_id']
    if data['type'].startswith('poll_'):
        keyboard = call['message']['reply_markup']['inline_keyboard']
        selected = [
            json.loads(button[0]['callback_data']).get('selected', 0)
            for button in keyboard
        ]
        max_selected = max(selected)
        if data['type'] == 'poll_answer':
            if max_selected >= 5:
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
        elif data['type'] == 'poll_clear':
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
        elif data['type'] == 'poll_ok':
            if max_selected < 5:
                return
            result = [(key, val) for key, val in enumerate(selected) if val != 0]
            result.sort(key=lambda x: x[1])
            username = call['from']['username']
            database_user_key = f"{username}"
            result_to_save = [val[0] for val in result]
            redis_tools.save_polling_result(redis_connection, database_user_key, result_to_save)
            logging.info(f"User with nickname {username} finished the poll. Result: {result}")
            print(f"User with nickname {username} finished the poll. Result: {result}")
            await bot.send_message(chat_id, msgs.after_poll_msg)
    elif data['type'] == 'steps':
        if data['step'] == 0:
            await bot.send_message(chat_id, msgs.poll_msg, reply_markup=msgs.poll)
    elif data['type'].startswith('variant_'):
        keyboard = call['message']['reply_markup']['inline_keyboard']
        if data['type'] == 'variant_switch':
            key = data['variant']
            btn_to_switch = keyboard[key][0]
            btn_data = json.loads(btn_to_switch['callback_data'])
            btn_data['selected'] = not btn_data['selected']
            if btn_data['selected']:
                btn_to_switch['text'] = '✅ ' + btn_to_switch['text']
            else:
                btn_to_switch['text'] = btn_to_switch['text'].removeprefix('✅ ')
            btn_to_switch['callback_data'] = json.dumps(btn_data)
            keyboard[key][0] = btn_to_switch
            keyb_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
            await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=keyb_markup)
        elif data['type'] == 'variant_ok':
            selected = [
                btn[0]['text'].removeprefix('✅ ')
                for btn in keyboard
                if json.loads(btn[0]['callback_data']).get('selected', False)
            ]
            redis_tools.save_final_variants(redis_connection, selected)
            await bot.send_message(
                chat_id,
                'Done!\nSend poll with variants to everyone?',
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[{
                    'text': 'Send',
                    'callback_data': json.dumps({'type': 'broadcast_poll_2'})
                }]])
            )
    elif data['type'] == 'broadcast_poll_2':
        variants = redis_tools.get_final_variants(redis_connection)
        users = redis_tools.get_all_users(redis_connection)
        variants_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [{'text': variant, 'callback_data': json.dumps({'type': 'poll2_choice', 'key': key, 'selected': 0})}]
            for key, variant in enumerate(variants)
        ]).row(
            types.InlineKeyboardButton(text='Clear', callback_data=json.dumps({'type': 'poll2_clear'})),
            types.InlineKeyboardButton("Send", callback_data=json.dumps({'type': 'poll2_ok'}))
        )
        for user in users:
            user_chat_id = redis_tools.get_user_chat_id(redis_connection, user)
            if user_chat_id:
                await bot.send_message(
                    user_chat_id, 'Choose 3 variants', reply_markup=variants_keyboard
                )
        #await bot.send_message(
        #    chat_id, 'Choose variants', reply_markup=variants_keyboard
        #)
    elif data['type'].startswith('poll2_'):
        keyboard = call['message']['reply_markup']['inline_keyboard']
        selected = [
            json.loads(button[0]['callback_data']).get('selected', 0)
            for button in keyboard
        ]
        max_selected = max(selected)
        if data['type'] == 'poll2_choice':
            if max_selected >= 3:
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
        elif data['type'] == 'poll2_clear':
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
        elif data['type'] == 'poll2_ok':
            if max_selected < 3:
                return
            result = [(key, val) for key, val in enumerate(selected) if val != 0]
            result.sort(key=lambda x: x[1])
            username = call['from']['username']
            database_user_key = f"{username}"
            result_to_save = [val[0] for val in result]
            redis_tools.save_polling_result(redis_connection, database_user_key, result_to_save, key='second')
            logging.info(f"User with nickname {username} finished the poll. Result: {result}")
            print(f"User with nickname {username} finished the poll 2. Result: {result}")
            await bot.send_message(chat_id, msgs.after_poll_msg)
            
@dp.message_handler(commands=['group_1'])
async def create_groups_of_different(message):
    '''
    Admin command.
    Cluster all users into groups of different users, send each of them their group number.
    '''
    usernames = redis_tools.get_all_users(redis_connection)
    # await message.reply('All users: ' + ', '.join(usernames))

    # Get poll results
    users = redis_tools.get_all_poll_results(redis_connection)
    
    await message.reply(f'All users answers:\n {users}\n starting clustering...')
    
    num_of_users = len(users.keys())
    
    # Users per group
    humans_per_group = 3
    
    target_groups = int(num_of_users/humans_per_group)
    num_of_clusters = target_groups * humans_per_group
    await message.reply(f'Number of users: {num_of_users}\nTarget groups: {target_groups}\n\
        humans per group: {humans_per_group}\n\
        Number of clusters: {num_of_clusters}')
    
    cluster_assignments = magic.cluster_vectors(list(users.values()), num_of_clusters)
    
    clustered_users = magic.cluster_users(users, num_of_clusters)
    user_clusters = magic.create_user_clusters(users, num_of_clusters)
    
    await message.reply(f'User clusters: {user_clusters}')
    
    await message.reply(f'Int results:\n{ magic.print_clusters(list(users.values()),cluster_assignments , print_flag = False )}')
    
    sorted_users = clustered_users.copy()
    
    # Save group numbers to redis
    
    for user in sorted_users:
        redis_tools.save_user_group(redis_connection, user, sorted_users[user])

    # Send messages to users with their group number
    
    for user in sorted_users:
        group_number = sorted_users[user]
        chat_id = redis_tools.get_user_chat_id(redis_connection, user)
        await bot.send_message(chat_id, f'Ваш номер группы: {group_number}')
    
    await message.reply('Users notified about their group number.')

@dp.message_handler(commands=['group_2'])
async def create_groups_of_similar(message):
    '''
    Admin command.
    Cluster all users into groups of similar users, send each of them their group number.
    '''
    pass

@dp.message_handler(commands=['/changeteamto'])
async def change_team(message):
    '''Changes user's team to group N'''
    pass

@dp.message_handler(commands=['add_variant'])
async def add_variant(message):
    print(message)
    variant = message['text'].removeprefix('/add_variant').strip()
    redis_tools.add_variant(redis_connection, variant, redis_tools.VARIANTS)
    await message.reply('Got it')

@dp.message_handler(commands=['get_variants'])
async def get_variants(message):
    '''Admin command'''
    variants = redis_tools.get_variants(redis_connection)
    await message.reply(
        'Select final variants',
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [{
                    'text': item,
                    'callback_data': json.dumps({
                        'type': 'variant_switch',
                        'variant': key,
                        'selected': False
                    })
                }]
                for key, item in enumerate(variants)
            ]
        ).row(
            types.InlineKeyboardButton(
                'Confirm selection',
                callback_data=json.dumps({'type': 'variant_ok'})
            )
        )
    )

@dp.message_handler(commands=['show_results'])
async def show_results(message):
    user_info = get_user_info(message)
    database_user_key = f"{user_info['user_username']}".strip()
    if not redis_tools.check_if_user_exists(redis_connection, database_user_key, redis_tools.ALL_USERS):
        redis_tools.add_user_to_group(redis_connection, database_user_key, redis_tools.ALL_USERS)
    poll_results = redis_tools.get_user_results(redis_connection, database_user_key)
    await message.reply(str(poll_results))

@dp.message_handler(commands=['clear_all'])
async def clear_all(message):
    print(message)
    await message.reply('Did it')
    keys = redis_connection.keys('*')
    redis_connection.delete(*keys)

# Start the bot

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    