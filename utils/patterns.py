import redis

from utils.db import PostgresDB


class PatternSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PatternSingleton, cls).__new__(cls)
        return cls._instance


class RepositoryDB:
    def __init__(self, redis_db: redis.Redis, postgres_db: PostgresDB):
        self.redis_db = redis_db
        self.postgres_db = postgres_db
