import datetime
import logging
import time

import psycopg2


class PostgresDB:
    def __init__(self, dbname, user, password, host, port):
        try:
            self.conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            print('Подключение к PostgreSQL успешно')
            self.initialize_tables()
        except Exception as e:
            print('Ошибка подключения к PostgreSQL', e)

    def _try_transaction(self, cur, query: str, values: tuple):
        try:
            cur.execute(query, values)
        except Exception as e:
            self.conn.rollback()
            logging.error(f'{self.__class__.__qualname__} {e}')
            raise Exception('Ошибка выполнения запроса в БД')
        else:
            self.conn.commit()

    def _drop_tables(self):
        with self.conn.cursor() as cur:
            query = '''
            DROP TABLE IF EXISTS users, user_requests;
            '''
            cur.execute(query)
            self.conn.commit()

    def _is_table_exists(self, table_name):
        with self.conn.cursor() as cur:
            query = f'''
                        SELECT EXISTS (
                            SELECT 1
                            FROM   information_schema.tables
                            WHERE  table_schema = 'public'
                            AND    table_name = '{table_name}'
                        )
                    '''
            cur.execute(query)
            return cur.fetchone()[0]

    def initialize_tables(self):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                    CREATE TABLE IF NOT EXISTS users
                    (
                        user_id bigint,
                        firstname text,
                        surname text,
                        username text,
                        date_registration timestamp DEFAULT (timezone('utc', NOW())),
                        date_update timestamp DEFAULT (timezone('utc', NOW())),
                        time_registration_unix numeric,
                        time_update_unix numeric,
                        ban boolean DEFAULT False,
                        PRIMARY KEY (user_id)
                    );
                    CREATE TABLE IF NOT EXISTS user_requests
                    (
                        request_id bigint,
                        request_data bytea,
                        user_id bigint REFERENCES users (user_id) ON UPDATE CASCADE,
                        CONSTRAINT user_requests_pkey PRIMARY KEY (request_id, user_id)
                    );
                """
            )
        self.conn.commit()

    def add_new_request(self, user_id, request_id, request_data):
        with self.conn.cursor() as cur:
            query = '''
                        INSERT INTO user_requests (request_id, request_data, user_id)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    '''
            values = (request_id, psycopg2.Binary(request_data), user_id)
            self._try_transaction(cur, query, values)

    def delete_request_for_user(self, user_id, request_id):
        with self.conn.cursor() as cur:
            query = '''
                        DELETE FROM user_requests
                        WHERE request_id = %s AND user_id = %s
                    '''
            values = (request_id, user_id)
            self._try_transaction(cur, query, values)

    def delete_request_for_all_users(self, request_id):
        with self.conn.cursor() as cur:
            query = '''
                        DELETE FROM user_requests
                        WHERE request_id = %s
                    '''
            values = (request_id,)
            self._try_transaction(cur, query, values)

    def get_all_requests(self):
        with self.conn.cursor() as cur:
            query = '''
                        SELECT * FROM user_requests
                    '''
            cur.execute(query)
            return cur.fetchall()

    def add_user(self, user_id, firstname, surname, username, time_info: TimeInfo):
        with self.conn.cursor() as cur:
            query = '''
                        INSERT INTO users (user_id, firstname, surname, username, date_registration, date_update,
                            time_registration_unix, time_update_unix)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    '''
            values = (user_id, firstname, surname, username, time_info.create_time, time_info.update_time,
                      time_info.create_time_unix, time_info.update_time_unix)
            self._try_transaction(cur, query, values)

    def delete_user(self, user_id):
        with self.conn.cursor() as cur:
            query = '''
                        DELETE FROM users
                        WHERE user_id = %s
                    '''
            values = (user_id,)
            self._try_transaction(cur, query, values)

    def update_user(self, user_id: int, date_update: datetime, time_update_unix: time,
                    firstname=None, surname=None, username=None, ban=None):
        with self.conn.cursor() as cur:
            fields = 'date_update = %s, time_update_unix = %s, '
            values = [date_update, time_update_unix]
            if firstname:
                fields += 'firstname = %s, '
                values.append(firstname)
            if surname:
                fields += 'surname = %s, '
                values.append(surname)
            if username:
                fields += 'username = %s, '
                values.append(username)
            if ban is not None:
                fields += 'ban = %s, '
                values.append(ban)
            query = f'''
                        UPDATE users
                        SET {fields[:-2]}
                        WHERE user_id = {user_id}
                    '''
            self._try_transaction(cur, query, tuple(values))

    def get_all_users(self):
        with self.conn.cursor() as cur:
            query = '''
                        SELECT * FROM users
                    '''
            cur.execute(query)
            return cur.fetchall()

    def get_user(self, user_id):
        with self.conn.cursor() as cur:
            query = '''
                        SELECT * FROM users
                        WHERE user_id = %s
                    '''
            values = (user_id,)
            cur.execute(query, values)
            return cur.fetchone()
