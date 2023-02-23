

# Deployment

1. Create `.env` file from `.env.example` and fill in the secret.
2. `docker-compose up -d --build` to start the server.
3. Go to @EVNCommUnion_bot and send `/start` to start the bot.


# Code structure

## `telegram_bot_app`

Bot is described in `telegram_bot_app/bot.py`. With a simple class with `start` method to demonstrate some workflows.


# Working with the database

Add database related code are in `telegram_bot_app/redis_tools.py`. The database is Redis.
I've created a simple wrapper for Redis, so you can use it like a dictionary.

```python
 if not redis_tools.check_if_user_exists(redis_connection, database_user_key, redis_tools.ALL_USERS):
     redis_tools.add_user_to_group(redis_connection, database_user_key, redis_tools.ALL_USERS)
```
To check if user exisis in built in key `ALL_USERS` and add user to it if not.

## Key standards

Telegram username is used as a user key in database.

For my own keys I use `_{key}_` format. To avoid collision with telegram usernames. For example:

```python
ALL_USERS = "_telegram_users_"
GLOBAL_DATABASE_LOCK = "_global_database_lock_"
```


For storing some user data you can use `{user}_conversation` as a key for conversation with a user. For example, if user with id `123` is in conversation with bot, you can store his data in `123_conversation` key.




# Requirements

1. Install [Docker](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/install/).