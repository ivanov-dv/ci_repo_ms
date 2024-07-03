import os
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

'''
BINANCE API WEIGHTS
'''
WEIGHT_GET_TICKER = 2
WEIGHT_REQUEST_KLINE = 6


'''
REDIS
'''
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0


'''
POSTGRESQL
'''
POSTGRESQL_USER = os.getenv('POSTGRESQL_USER')
POSTGRESQL_PASSWORD = os.getenv('POSTGRESQL_PASSWORD')
POSTGRESQL_DB = 'ci'
POSTGRESQL_HOST = 'localhost'
POSTGRESQL_PORT = 5432


'''
POSTGRESQL TEST
'''
POSTGRESQL_USER_TEST = os.getenv('POSTGRESQL_USER_TEST')
POSTGRESQL_PASSWORD_TEST = os.getenv('POSTGRESQL_PASSWORD_TEST')
POSTGRESQL_DB_TEST = 'ci_test'
POSTGRESQL_HOST_TEST = 'localhost'
POSTGRESQL_PORT_TEST = 5432
