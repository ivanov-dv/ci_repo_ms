from sqlalchemy import create_engine, update
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.dialects.postgresql import insert


class AlchemySqlDb:
    def __init__(self, sql_url, base: type[DeclarativeBase]):
        self.metadata = base.metadata
        self.engine = create_engine(sql_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def prepare(self):
        self.metadata.create_all(self.engine)

    def clear(self):
        self.metadata.drop_all(self.engine)
        self.metadata.create_all(self.engine)

    @staticmethod
    def insert_query(model, values: dict, index_elements: list):
        return (
            insert(model)
            .values(**values)
            .on_conflict_do_nothing(index_elements=index_elements)
        )

    @staticmethod
    def update_query(model, where_col, where_value, values):
        return update(model).values(values).where(where_col, where_value)

