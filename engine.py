import redis
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

import config as cfg

from sql.database import AlchemySqlDb
from sql.models import Base
from utils.repositories import Repository

sql_db = AlchemySqlDb(cfg.SQLALCHEMY_DATABASE_URL, Base)
redis_db = redis.Redis(host=cfg.REDIS_HOST, port=cfg.REDIS_HOST, db=cfg.REDIS_DB)
repo = Repository(redis_db, sql_db)

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

"""
PREPARING
"""
repo.sql_db.prepare()
repo.load_users_from_db()
repo.load_requests_from_db()