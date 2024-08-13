from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

import config as cfg

from sql.database import AlchemySqlDb
from sql.models import Base
from utils.repositories import Repository

sql_db = AlchemySqlDb(cfg.SQLALCHEMY_DATABASE_URL, Base)
repo = Repository(sql_db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await repo.sql_db.prepare()
    await repo.load_users_from_db()
    await repo.load_requests_from_db()
    yield
    print("Application shutdown")


app = FastAPI(lifespan=lifespan)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
