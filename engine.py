import redis
from fastapi import FastAPI

import config as cfg
from utils.db import PostgresDB
from utils.repositories import RequestRepository, UserRepository

postgres_db = PostgresDB(
    dbname=cfg.POSTGRESQL_DB,
    user=cfg.POSTGRESQL_USER,
    password=cfg.POSTGRESQL_PASSWORD,
    host=cfg.POSTGRESQL_HOST,
    port=cfg.POSTGRESQL_PORT
)

redis_db = redis.Redis(
    host=cfg.REDIS_HOST,
    port=cfg.REDIS_HOST,
    db=cfg.REDIS_DB
)

users_repo = UserRepository(redis_db, postgres_db)
request_repo = RequestRepository(redis_db, postgres_db)
app = FastAPI()

'''
PREPARING
'''
users_repo.load_users_from_db()


from utils.models import *
from pprint import pprint
#
# request_repo.add(1, UserRequest(Symbol('BTCUSDT'), Price(65000), Way.up_to))
# request_repo.add(2, UserRequest(Symbol('BTCUSDT'), Price(65000), Way.up_to))
# request_repo.add(3, UserRequest(Symbol('BTCUSDT'), Price(65000), Way.up_to))
# request_repo.add(4, UserRequest(Symbol('BTCUSDT'), Price(65000), Way.up_to))
# request_repo.add(3, UserRequest(Symbol('BTCUSDT'), PercentOfTime(28, Period.v_24h), Way.down_to))
# request_repo.add(4, UserRequest(Symbol('BTCUSDT'), Price(65000), Way.down_to))

# postgres_db.add_user(123, 'denis', 'ivanov', 'ivanov_dv')
