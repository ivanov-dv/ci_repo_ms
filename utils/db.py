import datetime
import logging
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
            DROP TABLE IF EXISTS users, requests, users_requests;
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
                f"""
                    CREATE TABLE IF NOT EXISTS users
                    (
                        user_id bigint,
                        firstname text,
                        surname text,
                        username text,
                        date_registration timestamp DEFAULT (timezone('utc', NOW())),
                        date_update timestamp DEFAULT (timezone('utc', NOW())),
                        ban boolean DEFAULT False,
                        PRIMARY KEY (user_id)
                    );
                    CREATE TABLE IF NOT EXISTS requests 
                    (
                        request_id bigint,
                        request_data bytea,
                        status_add_new boolean DEFAULT False,
                        PRIMARY KEY (request_id)
                    );
                    CREATE TABLE IF NOT EXISTS users_requests
                    (
                        request_id bigint REFERENCES requests (request_id) ON UPDATE CASCADE,
                        user_id bigint REFERENCES users (user_id) ON UPDATE CASCADE,
                        CONSTRAINT users_requests_pkey PRIMARY KEY (request_id, user_id)
                    );
                """
            )
        self.conn.commit()

    def add_new_request(self, user_id, request_id, request_data):
        with self.conn.cursor() as cur:
            query1 = '''
                        INSERT INTO requests (request_id, request_data)
                        VALUES (%s, %s)
                    '''
            values1 = (request_id, psycopg2.Binary(request_data))
            self._try_transaction(cur, query1, values1)
            query2 = '''
                        INSERT INTO users_requests (request_id, user_id)
                        VALUES (%s, %s);
                        UPDATE requests
                        SET status_add_new = True
                        WHERE request_id = %s
                    '''
            values2 = (request_id, user_id, request_id)
            self._try_transaction(cur, query2, values2)

    def add_request_to_user(self, request_id, user_id):
        with self.conn.cursor() as cur:
            query = '''
                        INSERT INTO users_requests (request_id, user_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    '''
            values = (request_id, user_id)
            self._try_transaction(cur, query, values)

    def delete_request(self, user_id, request_id):
        with self.conn.cursor() as cur:
            query = '''
                        DELETE FROM users_requests
                        WHERE request_id = %s AND user_id = %s
                    '''
            values = (request_id, user_id)
            self._try_transaction(cur, query, values)

    def add_user(self, user_id, firstname, surname, username, date_registration, date_update):
        with self.conn.cursor() as cur:
            query = '''
                        INSERT INTO users (user_id, firstname, surname, username, date_registration, date_update)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    '''
            values = (user_id, firstname, surname, username, date_registration, date_update)
            self._try_transaction(cur, query, values)

    def delete_user(self, user_id):
        with self.conn.cursor() as cur:
            query = '''
                        DELETE FROM users
                        WHERE user_id = %s
                    '''
            values = (user_id,)
            self._try_transaction(cur, query, values)

    def update_user(self, user_id, firstname=None, surname=None, username=None, ban=None):
        with self.conn.cursor() as cur:
            fields = 'date_update = %s, '
            values = [datetime.datetime.utcnow()]
            if firstname:
                fields += f'firstname = %s, '
                values.append(firstname)
            if surname:
                fields += f'surname = %s, '
                values.append(surname)
            if username:
                fields += f'username = %s, '
                values.append(username)
            if ban is not None:
                fields += f'ban = %s, '
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
