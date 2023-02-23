import time,logging

# Defines
ALL_USERS = "_telegram_users_"
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

def set_last_interaction(redis_connection, user, timestamp):
    """Set last interaction timestamp for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.set(f"{user}_last_interaction", timestamp)

def delete_interactions(redis_connection, user):
    """Delete interactions for user"""
    with redis_connection.lock(GLOBAL_DATABASE_LOCK, blocking=True , timeout=10) as lock:
        redis_connection.delete(f"{user}_last_interaction")
        redis_connection.delete(f"{user}_conversation")
        redis_connection.lrem(ALL_USERS, 0, user)

