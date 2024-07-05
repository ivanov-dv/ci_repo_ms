from decimal import Decimal

import pytest
import redis

from utils.db import *
from utils.repositories import *

'''
CONFIG
'''
postgres_db = PostgresDB(
    dbname=config.POSTGRESQL_DB_TEST,
    user=config.POSTGRESQL_USER_TEST,
    password=config.POSTGRESQL_PASSWORD_TEST,
    host=config.POSTGRESQL_HOST_TEST,
    port=config.POSTGRESQL_PORT_TEST
)

redis_db = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_HOST,
    db=config.REDIS_DB
)


class TestRequest:
    @staticmethod
    def test_comparison_request_server():
        ex1 = RequestForServer(
            UniqueUserRequest(UserRequest(Symbol('BtcUsdT'), Price(70000.1), Way.down_to))
        )
        ex2 = RequestForServer(
            UniqueUserRequest(UserRequest(Symbol('BTCUSDT'), Price(60000.1), Way.up_to))
        )
        ex3 = RequestForServer(
            UniqueUserRequest(UserRequest(Symbol('BtcUsdT'), PercentOfPoint(23.5, 65000), Way.up_to))
        )
        ex4 = RequestForServer(
            UniqueUserRequest(UserRequest(Symbol('BTCUSDT'), PercentOfPoint(-3.5, 65000), Way.up_to))
        )
        ex5 = RequestForServer(
            UniqueUserRequest(UserRequest(Symbol('BTCUSDT'), PercentOfTime(-3.5, Period.v_24h), Way.up_to))
        )
        ex6 = RequestForServer(
            UniqueUserRequest(UserRequest(Symbol('BTCUSDT'), PercentOfTime(-3.5, Period.v_4h), Way.up_to))
        )
        ex7 = RequestForServer(
            UniqueUserRequest(UserRequest(Symbol('BTCUSDT'), PercentOfTime(-3.5, Period.v_4h), Way.up_to))
        )
        assert ex1 == ex2
        assert ex3 == ex4
        assert ex1 == ex3
        assert ex1 != ex5
        assert ex4 != ex5
        assert ex5 != ex6
        assert ex6 == ex7

    @staticmethod
    def test_comparison_user_request():
        ex1 = UserRequest(Symbol('BTcuSDT'), PercentOfTime(20.5, Period.v_24h), Way.up_to)
        ex2 = UserRequest(Symbol('btcuSDT'), PercentOfTime(20.5, Period.v_24h), Way.up_to)
        ex3 = UserRequest(Symbol('btcuSDT'), PercentOfTime(20.4, Period.v_24h), Way.up_to)
        assert ex1 == ex2
        assert ex2 != ex3

    @staticmethod
    @pytest.mark.parametrize(
        "ex1, ex2",
        [
            (RequestForServer(UniqueUserRequest(UserRequest(Symbol('BTCUSDT'), Price(60000.1), Way.up_to))),
             RequestForServer(UniqueUserRequest(UserRequest(Symbol('BTCUSD'), Price(60000.1), Way.up_to)))),
            (RequestForServer(UniqueUserRequest(UserRequest(Symbol('BTCUSDT'), PercentOfPoint(-3.5, 70000), Way.up_to))),
             RequestForServer(UniqueUserRequest(UserRequest(Symbol('EThUSDT'), PercentOfPoint(-3.5, 70000), Way.up_to)))),
            (UserRequest(Symbol('BTcuSDt'), PercentOfTime(20.5, Period.v_24h), Way.up_to),
             UserRequest(Symbol('BTcuSDT'), PercentOfTime(20.5, Period.v_4h), Way.up_to))
        ]
    )
    def test_comparison_requests_different(ex1, ex2):
        assert ex1 != ex2


class TestRequestRepository:
    request_repo = RequestRepository(redis_db, postgres_db)
    pg_db = postgres_db
    time_info = TimeInfo()

    pg_db._drop_tables()
    pg_db.initialize_tables()

    user_request1 = UserRequest(Symbol('btcusdt'), PercentOfTime(23, Period.v_24h), Way.up_to)
    user_request2 = UserRequest(Symbol('btcusdt'), PercentOfTime(23, Period.v_24h), Way.up_to)
    user_request3 = UserRequest(Symbol('btcusdt'), PercentOfPoint(23, 70000), Way.up_to)
    user_request4 = UserRequest(Symbol('ethusdt'), PercentOfPoint(23, 70000), Way.up_to)
    user_request5 = UserRequest(Symbol('btcusdt'), Price(69000), Way.up_to)
    user_request6 = UserRequest(Symbol('btcusdt'), Price(68000), Way.down_to)
    user_request7 = UserRequest(Symbol('ETHUsdt'), PercentOfTime(23, Period.v_24h), Way.up_to)

    def test_add(self):
        self.pg_db.add_user(1, 'sergey', 'ivanov', 'sergey_ivanov', self.time_info)
        self.pg_db.add_user(2, 'ivan', 'petrov', 'ivan_petrov', self.time_info)
        self.pg_db.add_user(3, 'fedor', 'sidorov', 'fedor_sidorov', self.time_info)

        self.request_repo.user_requests = {}
        self.request_repo.unique_user_requests = {}

        self.request_repo.add(1, self.user_request1)
        self.request_repo.add(1, self.user_request2)
        self.request_repo.add(1, self.user_request3)
        self.request_repo.add(1, self.user_request4)
        self.request_repo.add(1, self.user_request5)
        self.request_repo.add(1, self.user_request6)
        self.request_repo.add(2, self.user_request2)
        self.request_repo.add(2, self.user_request4)
        self.request_repo.add(2, self.user_request5)

        res_user_requests = {
            1: {UserRequest(Symbol('btcusdt'), PercentOfTime(23, Period.v_24h), Way.up_to),
                UserRequest(Symbol('btcusdt'), PercentOfPoint(23, 70000), Way.up_to),
                UserRequest(Symbol('ethusdt'), PercentOfPoint(23, 70000), Way.up_to),
                UserRequest(Symbol('btcusdt'), Price(69000), Way.up_to),
                UserRequest(Symbol('btcusdt'), Price(68000), Way.down_to)},
            2: {UserRequest(Symbol('btcusdt'), PercentOfTime(23, Period.v_24h), Way.up_to),
                UserRequest(Symbol('ethusdt'), PercentOfPoint(23, 70000), Way.up_to),
                UserRequest(Symbol('btcusdt'), Price(69000), Way.up_to)}
        }
        res_unique = {
            UniqueUserRequest(UserRequest(Symbol('btcusdt'), PercentOfTime(23, Period.v_24h), Way.up_to)): {1, 2},
            UniqueUserRequest(UserRequest(Symbol('btcusdt'), PercentOfPoint(23, 70000), Way.up_to)): {1},
            UniqueUserRequest(UserRequest(Symbol('ethusdt'), PercentOfPoint(23, 70000), Way.up_to)): {1, 2},
            UniqueUserRequest(UserRequest(Symbol('btcusdt'), Price(69000), Way.up_to)): {1, 2},
            UniqueUserRequest(UserRequest(Symbol('btcusdt'), Price(68000), Way.down_to)): {1}
        }
        assert self.request_repo.user_requests == res_user_requests
        assert self.request_repo.unique_user_requests == res_unique
        assert ({r.request_id for r in self.request_repo.unique_user_requests.keys()} ==
                {r.request_id for sets in self.request_repo.user_requests.values() for r in sets})
        assert {r.request_id for r in self.request_repo.unique_user_requests.keys()} is not None
        assert {r.request_id for sets in self.request_repo.user_requests.values() for r in sets} is not None
        assert self.request_repo.get(1, self.user_request1) == self.user_request1
        assert self.request_repo.get(1, self.user_request7) is None
        assert self.request_repo.get_all_requests_for_user_id(2) == res_user_requests[2]
        assert (self.request_repo.get(1, self.user_request2).request_id ==
                self.request_repo.get(2, self.user_request2).request_id)
        assert (self.request_repo.get(2, self.user_request2).request_id !=
                self.request_repo.get(2, self.user_request4).request_id)

        self.request_repo.delete(1, self.user_request2)  # req2 = req1
        self.request_repo.delete(1, self.user_request3)
        self.request_repo.delete(1, self.user_request5)
        self.request_repo.delete(2, self.user_request2)
        self.request_repo.delete(2, self.user_request4)
        self.request_repo.delete(2, self.user_request5)

        res_user_requests_delete = {
            1: {self.user_request4, self.user_request6}
        }
        res_unique_delete = {
            UniqueUserRequest(UserRequest(Symbol('ethusdt'), PercentOfPoint(23, 70000), Way.up_to)): {1},
            UniqueUserRequest(UserRequest(Symbol('btcusdt'), Price(68000), Way.down_to)): {1}
        }

        assert self.request_repo.user_requests == res_user_requests_delete
        assert self.request_repo.unique_user_requests == res_unique_delete

    def test_get(self):
        assert self.request_repo.get(1, self.user_request4) == self.user_request4

    def test_get_all_requests_for_user_id(self):
        self.request_repo.add(1, self.user_request1)
        assert len(self.request_repo.get_all_requests_for_user_id(1)) == 3
        self.request_repo.delete(1, self.user_request1)
        assert len(self.request_repo.get_all_requests_for_user_id(1)) == 2

    def test_get_all_users_for_request(self):
        assert self.request_repo.get_all_users_for_request(self.user_request4) == {1}
        self.request_repo.add(2, self.user_request4)
        self.request_repo.add(3, self.user_request4)
        assert self.request_repo.get_all_users_for_request(self.user_request4) == {1, 2, 3}
        self.request_repo.delete(2, self.user_request4)
        assert self.request_repo.get_all_users_for_request(self.user_request4) == {1, 3}


class TestUserRepository:
    user_repo = UserRepository(redis_db, postgres_db)

    def test_add_without_db(self):
        pass


class TestDB:
    pg_db = postgres_db
    time_info = TimeInfo()
    dt = datetime.datetime(2024, 7, 4, 14, 55, 6, 742449)
    time_info.create_time_unix = 123
    time_info.update_time_unix = 123

    def test_initialize_db(self):
        self.pg_db._drop_tables()
        self.pg_db.initialize_tables()
        assert self.pg_db._is_table_exists('users')
        assert self.pg_db._is_table_exists('user_requests')

    def test_add_user(self):
        self.pg_db.initialize_tables()

        self.pg_db.add_user(1, 'sergey', 'ivanov', 'sergey_ivanov', self.time_info)
        self.pg_db.add_user(2, 'ivan', 'petrov', 'ivan_petrov', self.time_info)
        self.pg_db.add_user(3, 'fedor', 'sidorov', 'fedor_sidorov', self.time_info)

        with pytest.raises(Exception, match='Ошибка выполнения запроса в БД'):
            self.pg_db.add_user(2, 'fedor', 'sidorov', 'fedor_sidorov', self.time_info)

        assert (self.pg_db.get_user(1) ==
                (1, 'sergey', 'ivanov', 'sergey_ivanov', self.time_info.create_time, self.time_info.update_time, Decimal(self.time_info.create_time_unix), Decimal(self.time_info.update_time_unix), False))
        assert (self.pg_db.get_user(2) ==
                (2, 'ivan', 'petrov', 'ivan_petrov', self.time_info.create_time, self.time_info.update_time, Decimal(self.time_info.create_time_unix), Decimal(self.time_info.update_time_unix), False))
        assert (self.pg_db.get_user(3) ==
                (3, 'fedor', 'sidorov', 'fedor_sidorov', self.time_info.create_time, self.time_info.update_time, Decimal(self.time_info.create_time_unix), Decimal(self.time_info.update_time_unix), False))

        all_users = [
            (1, 'sergey', 'ivanov', 'sergey_ivanov', self.time_info.create_time, self.time_info.update_time, Decimal(self.time_info.create_time_unix), Decimal(self.time_info.update_time_unix), False),
            (2, 'ivan', 'petrov', 'ivan_petrov', self.time_info.create_time, self.time_info.update_time, Decimal(self.time_info.create_time_unix), Decimal(self.time_info.update_time_unix), False),
            (3, 'fedor', 'sidorov', 'fedor_sidorov', self.time_info.create_time, self.time_info.update_time, Decimal(self.time_info.create_time_unix), Decimal(self.time_info.update_time_unix), False)]
        assert self.pg_db.get_all_users() == all_users

    def test_update_and_get_user(self):
        self.pg_db.initialize_tables()
        self.pg_db.update_user(2, firstname='alexey', ban=True, date_update=self.dt, time_update_unix=123)

        assert self.pg_db.get_user(2) == (2, 'alexey', 'petrov', 'ivan_petrov', self.time_info.create_time, self.dt, Decimal(self.time_info.create_time_unix), Decimal(123), True)

    def test_delete_user(self):
        self.pg_db.initialize_tables()
        self.pg_db.delete_user(2)

        all_users = [
            (1, 'sergey', 'ivanov', 'sergey_ivanov', self.time_info.create_time, self.time_info.update_time, Decimal(self.time_info.create_time_unix), Decimal(self.time_info.update_time_unix), False),
            (3, 'fedor', 'sidorov', 'fedor_sidorov', self.time_info.create_time, self.time_info.update_time, Decimal(self.time_info.create_time_unix), Decimal(self.time_info.update_time_unix), False)]

        assert self.pg_db.get_all_users() == all_users
