from sql.database import AlchemySqlDb


class PatternSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PatternSingleton, cls).__new__(cls)
        return cls._instance


class RepositoryDB:
    def __init__(self, sql_db: AlchemySqlDb):
        self.sql_db = sql_db

