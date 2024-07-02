import pytest

import config
from utils.db import *
from utils.repositories import *

'''
CONFIG
'''


class TestRequest:
    @staticmethod
    def test_comparison_request_server():
        ex1 = RequestForServer(UserRequest(Symbol('BtcUsdT'), Price(70000.1), Way.down_to))
        ex2 = RequestForServer(UserRequest(Symbol('BTCUSDT'), Price(60000.1), Way.up_to))
        ex3 = RequestForServer(UserRequest(Symbol('BtcUsdT'), PercentOfPoint(23.5, 65000), Way.up_to))
        ex4 = RequestForServer(UserRequest(Symbol('BTCUSDT'), PercentOfPoint(-3.5, 65000), Way.up_to))
        ex5 = RequestForServer(UserRequest(Symbol('BTCUSDT'), PercentOfTime(-3.5, Period.v_24h), Way.up_to))
        ex6 = RequestForServer(UserRequest(Symbol('BTCUSDT'), PercentOfTime(-3.5, Period.v_4h), Way.up_to))
        ex7 = RequestForServer(UserRequest(Symbol('BTCUSDT'), PercentOfTime(-3.5, Period.v_4h), Way.up_to))
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
            (RequestForServer(UserRequest(Symbol('BTCUSDT'), Price(60000.1), Way.up_to)),
             RequestForServer(UserRequest(Symbol('BTCUSD'), Price(60000.1), Way.up_to))),
            (RequestForServer(UserRequest(Symbol('BTCUSDT'), PercentOfPoint(-3.5, 70000), Way.up_to)),
             RequestForServer(UserRequest(Symbol('EThUSDT'), PercentOfPoint(-3.5, 70000), Way.up_to))),
            (UserRequest(Symbol('BTcuSDt'), PercentOfTime(20.5, Period.v_24h), Way.up_to),
             UserRequest(Symbol('BTcuSDT'), PercentOfTime(20.5, Period.v_4h), Way.up_to))
        ]
    )
    def test_comparison_requests_different(ex1, ex2):
        assert ex1 != ex2


class TestRequestRepository:
    request_repo = RequestRepository('db', 'db')

    user_request1 = UserRequest(Symbol('btcusdt'), PercentOfTime(23, Period.v_24h), Way.up_to)
    user_request2 = UserRequest(Symbol('btcusdt'), PercentOfTime(23, Period.v_24h), Way.up_to)
    user_request3 = UserRequest(Symbol('btcusdt'), PercentOfPoint(23, 70000), Way.up_to)
    user_request4 = UserRequest(Symbol('ethusdt'), PercentOfPoint(23, 70000), Way.up_to)
    user_request5 = UserRequest(Symbol('btcusdt'), Price(69000), Way.up_to)
    user_request6 = UserRequest(Symbol('btcusdt'), Price(68000), Way.down_to)
    user_request7 = UserRequest(Symbol('ETHUsdt'), PercentOfTime(23, Period.v_24h), Way.up_to)

    def test_add_without_db(self):
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
            UserRequest(Symbol('btcusdt'), PercentOfTime(23, Period.v_24h), Way.up_to): {1, 2},
            UserRequest(Symbol('btcusdt'), PercentOfPoint(23, 70000), Way.up_to): {1},
            UserRequest(Symbol('ethusdt'), PercentOfPoint(23, 70000), Way.up_to): {1, 2},
            UserRequest(Symbol('btcusdt'), Price(69000), Way.up_to): {1, 2},
            UserRequest(Symbol('btcusdt'), Price(68000), Way.down_to): {1}
        }
        assert self.request_repo.user_requests == res_user_requests
        assert self.request_repo.unique_user_requests == res_unique
        assert self.request_repo.get(1, self.user_request1) == self.user_request1
        assert self.request_repo.get(1, self.user_request7) is None
        assert self.request_repo.get_all_for_user_id(2) == res_user_requests[2]
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
            UserRequest(Symbol('ethusdt'), PercentOfPoint(23, 70000), Way.up_to): {1},
            UserRequest(Symbol('btcusdt'), Price(68000), Way.down_to): {1}
        }

        assert self.request_repo.user_requests == res_user_requests_delete
        assert self.request_repo.unique_user_requests == res_unique_delete


class TestUserRepository:
    user_repo = UserRepository('db', 'db')

    def test_add_without_db(self):
        pass


class TestDB:
    postgres_db = PostgresDB(
        config.POSTGRESQL_DB_TEST,
        config.POSTGRESQL_USER_TEST,
        config.POSTGRESQL_PASSWORD_TEST,
        config.POSTGRESQL_HOST_TEST,
        config.POSTGRESQL_PORT_TEST
    )
    dt = datetime.datetime(2024, 7, 1, 12, 54, 26, 164025)

    def test_initialize_db(self):
        self.postgres_db._drop_tables()
        self.postgres_db.initialize_tables()
        assert self.postgres_db._is_table_exists('users')
        assert self.postgres_db._is_table_exists('users_requests')
        assert self.postgres_db._is_table_exists('requests')

    def test_add_user(self):
        self.postgres_db.initialize_tables()

        self.postgres_db.add_user(1, 'sergey', 'ivanov', 'sergey_ivanov', self.dt, self.dt)
        self.postgres_db.add_user(2, 'ivan', 'petrov', 'ivan_petrov', self.dt, self.dt)
        self.postgres_db.add_user(3, 'fedor', 'sidorov', 'fedor_sidorov', self.dt, self.dt)

        with pytest.raises(Exception, match='Ошибка выполнения запроса в БД'):
            self.postgres_db.add_user(2, 'fedor', 'sidorov', 'fedor_sidorov', self.dt, self.dt)

        assert self.postgres_db.get_user(1) == (1, 'sergey', 'ivanov', 'sergey_ivanov', self.dt, self.dt, False)
        assert self.postgres_db.get_user(2) == (2, 'ivan', 'petrov', 'ivan_petrov', self.dt, self.dt, False)
        assert self.postgres_db.get_user(3) == (3, 'fedor', 'sidorov', 'fedor_sidorov', self.dt, self.dt, False)

        all_users = [
            (1, 'sergey', 'ivanov', 'sergey_ivanov', self.dt, self.dt, False),
            (2, 'ivan', 'petrov', 'ivan_petrov', self.dt, self.dt, False),
            (3, 'fedor', 'sidorov', 'fedor_sidorov', self.dt, self.dt, False)]
        assert self.postgres_db.get_all_users() == all_users

    def test_update_and_get_user(self):
        self.postgres_db.initialize_tables()
        self.postgres_db.update_user(2, firstname='alexey', ban=True)
        dt_upd = self.postgres_db.get_user(2)[5]

        assert self.postgres_db.get_user(2) == (2, 'alexey', 'petrov', 'ivan_petrov', self.dt, dt_upd, True)

    def test_delete_user(self):
        self.postgres_db.initialize_tables()
        self.postgres_db.delete_user(2)

        all_users = [
            (1, 'sergey', 'ivanov', 'sergey_ivanov', self.dt, self.dt, False),
            (3, 'fedor', 'sidorov', 'fedor_sidorov', self.dt, self.dt, False)]

        assert self.postgres_db.get_all_users() == all_users

