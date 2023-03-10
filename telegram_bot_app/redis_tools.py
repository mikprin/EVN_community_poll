import time,logging

# Defines
ALL_USERS = "_telegram_users_"
VARIANTS = "_variants_"
GLOBAL_DATABASE_LOCK = "_global_database_lock_"
INTERACTION_TIMEOUT = 172800
FIRST_POLL = "_first_poll_group_"


# Functions
def add_user_to_group(redis_connection, user, collection):
    """Add user to redis"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.rpush(collection, user)

def get_all_users(redis_connection):
    """Get all users from redis"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        res = [ x.decode("utf-8") for x in redis_connection.lrange(ALL_USERS, 0, -1)]
    return res

def check_if_user_exists(redis_connection, user, collection):
    """Check if user exists in redis"""
    lst = [ x.decode("utf-8") for x in redis_connection.lrange(ALL_USERS, 0, -1)]
    if user in lst:
        return True
    return False

def save_user_chat_id(redis_connection, user, chat_id):
    """Save user chat id in redis"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.set(f"{user}_chat_id", chat_id)

def get_user_chat_id(redis_connection, user):
    """Get user chat id from redis"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        res = redis_connection.get(f"{user}_chat_id")
        if res:
            chat_id = int(res.decode("utf-8"))
            return chat_id
        else:
            return None

def remove_user_from_group(redis_connection, user, collection):
    """Remove user from redis"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.lrem(collection, 0, user)

def set_last_interaction(redis_connection, user, timestamp):
    """Set last interaction timestamp for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.set(f"{user}_last_interaction", timestamp)

def delete_interactions(redis_connection, user):
    """Delete interactions for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        # redis_connection.delete(f"{user}_last_interaction")
        # redis_connection.delete(f"{user}_conversation")
        redis_connection.delete(f"{user}_chat_id")
        redis_connection.lrem(ALL_USERS, 0, user)
        redis_connection.delete(f"{user}_init_polling")
        redis_connection.delete(f"{user}{FIRST_POLL}")

def save_polling_result(redis_connection, user, result: list[int], key: str = 'init'):
    """Save polling result for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:

        if redis_connection.exists(f"{user}_{key}_polling"):
            redis_connection.delete(f"{user}_{key}_polling")

        for i in result:
            redis_connection.rpush(f"{user}_{key}_polling", i)

def remove_user_results(redis_connection, user):
    """Remove polling result for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.delete(f"{user}_init_polling")

def get_user_results(redis_connection, user, key: str = 'init'):
    """Get polling result for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        bytes_list = redis_connection.lrange(f"{user}_{key}_polling", 0, -1)
        result = [int(x) for x in bytes_list]
        return result
    
def add_variant(redis_connection, variant, collection):
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.rpush(collection, variant)
        
def get_variants(redis_connection):
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        res = [ x.decode("utf-8") for x in redis_connection.lrange(VARIANTS, 0, -1)]
    return res

def remove_variants(redis_connection):
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.delete(VARIANTS)

def save_final_variants(redis_connection, variants: list[str]):
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        if redis_connection.exists("final_variants"):
            redis_connection.delete("final_variants")
        for i in variants:
            redis_connection.rpush("final_variants", i)
            
def get_final_variants(redis_connection):
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        res = [ x.decode("utf-8") for x in redis_connection.lrange("final_variants", 0, -1)]
        return res

def get_all_poll_results(redis_connection, collection="init"):
    """Get all polling results"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        users = [x.decode("utf-8") for x in redis_connection.lrange(ALL_USERS, 0, -1)]
    result = {}
    for user in users:
        user_poll = get_user_results(redis_connection, user, collection)
        if user_poll != []:
            result[user] = get_user_results(redis_connection, user, collection)
    return result


def save_user_group(redis_connection, user, group, collection):
    """Save user group"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.set(f"{user}{collection}", str(group))

def read_user_group(redis_connection, user, collection):
    """Read user group"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        res = redis_connection.get(f"{user}{collection}")
        if res:
            group = int(res.decode("utf-8"))
            return group
        else:
            return None