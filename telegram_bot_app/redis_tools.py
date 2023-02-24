import time,logging

# Defines
ALL_USERS = "_telegram_users_"
VARIANTS = "_variants_"
GLOBAL_DATABASE_LOCK = "_global_database_lock_"
INTERACTION_TIMEOUT = 172800

# Functions
def add_user_to_group(redis_connection, user, collection):
    """Add user to redis"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.rpush(collection, user)

def check_if_user_exists(redis_connection, user, collection):
    """Check if user exists in redis"""
    lst = [ x.decode("utf-8") for x in redis_connection.lrange(ALL_USERS, 0, -1)]
    if user in lst:
        return True
    return False

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
        redis_connection.lrem(ALL_USERS, 0, user)
        redis_connection.delete(f"{user}_init_polling")

def save_polling_result(redis_connection, user, result: list[int]):
    """Save polling result for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        if not redis_connection.exists(f"{user}_init_polling"):
            redis_connection.delete(f"{user}_init_polling")
        for i in result:
            redis_connection.rpush(f"{user}_init_polling", i)

def remove_user_results(redis_connection, user):
    """Remove polling result for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.delete(f"{user}_init_polling")

def get_user_results(redis_connection, user):
    """Get polling result for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        bytes_list = redis_connection.lrange(f"{user}_init_polling", 0, -1)
        result = [int(x) for x in bytes_list]
        return result
    
def add_variant(redis_connection, variant, collection):
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.rpush(collection, variant)
        
def get_variants(redis_connection):
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        res = [ x.decode("utf-8") for x in redis_connection.lrange(VARIANTS, 0, -1)]
        return res

def save_final_variants(redis_connection, variants: list[str]):
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        if not redis_connection.exists("final_variants"):
            redis_connection.delete("final_variants")
        for i in variants:
            redis_connection.rpush("final_variants", i)
            
def get_final_variants(redis_connection):
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        res = [ x.decode("utf-8") for x in redis_connection.lrange("final_variants", 0, -1)]
        return res

def get_all_poll_results(redis_connection):
    """Get all polling results"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        users = [x.decode("utf-8") for x in redis_connection.lrange(ALL_USERS, 0, -1)]
    result = {}
    for user in users:
        result[user] = get_user_results(redis_connection, user)
    return result
