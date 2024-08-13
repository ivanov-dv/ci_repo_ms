import datetime

import pytest
import redis

import config
from sql.database import AlchemySqlDb
from sql.models import Base, UserOrm
from utils.repositories import Repository
from utils.schemas import (
    RequestForServer,
    UniqueUserRequest,
    Price,
    Way,
    PercentOfTime,
    Period,
    PercentOfPoint,
    User,
    UserRequest,
)

"""
CONFIG
"""
test_sql = AlchemySqlDb(config.SQLALCHEMY_DATABASE_URL_TEST, Base, test=True)
redis_db = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_HOST, db=config.REDIS_DB)


class TestRequest:
    @staticmethod
    def test_comparison_request_server():
        ex1 = RequestForServer(
            UniqueUserRequest(
                UserRequest.create(
                    symbol="BtcUsdT",
                    request_data=Price(target_price=70000.1),
                    way=Way.down_to,
                )
            )
        )
        ex2 = RequestForServer(
            UniqueUserRequest(
                UserRequest.create(
                    symbol="BTCUSDT",
                    request_data=Price(target_price=60000.1),
                    way=Way.up_to,
                )
            )
        )
        ex3 = RequestForServer(
            UniqueUserRequest(
                UserRequest.create(
                    symbol="BtcUsdT",
                    request_data=PercentOfPoint(
                        target_percent=23.5, current_price=65000
                    ),
                    way=Way.up_to,
                )
            )
        )
        ex4 = RequestForServer(
            UniqueUserRequest(
                UserRequest.create(
                    symbol="BTCUSDT",
                    request_data=PercentOfPoint(
                        target_percent=-3.5, current_price=65000
                    ),
                    way=Way.up_to,
                )
            )
        )
        ex5 = RequestForServer(
            UniqueUserRequest(
                UserRequest.create(
                    symbol="BTCUSDT",
                    request_data=PercentOfTime(
                        target_percent=-3.5, period=Period.v_24h
                    ),
                    way=Way.up_to,
                )
            )
        )
        ex6 = RequestForServer(
            UniqueUserRequest(
                UserRequest.create(
                    symbol="BTCUSDT",
                    request_data=PercentOfTime(target_percent=-3.5, period=Period.v_4h),
                    way=Way.up_to,
                )
            )
        )
        ex7 = RequestForServer(
            UniqueUserRequest(
                UserRequest.create(
                    symbol="BTCUSDT",
                    request_data=PercentOfTime(target_percent=-3.5, period=Period.v_4h),
                    way=Way.up_to,
                )
            )
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
        ex1 = UserRequest.create(
            "BTcuSDT",
            PercentOfTime(target_percent=20.5, period=Period.v_24h),
            Way.up_to,
        )
        ex2 = UserRequest.create(
            "btcuSDT",
            PercentOfTime(target_percent=20.5, period=Period.v_24h),
            Way.up_to,
        )
        ex3 = UserRequest.create(
            "btcuSDT",
            PercentOfTime(target_percent=20.4, period=Period.v_24h),
            Way.up_to,
        )
        assert ex1 == ex2
        assert ex2 != ex3

    @staticmethod
    @pytest.mark.parametrize(
        "ex1, ex2",
        [
            (
                    RequestForServer(
                        UniqueUserRequest(
                            UserRequest.create(
                                "BTCUSDT", Price(target_price=60000.1), Way.up_to
                            )
                        )
                    ),
                    RequestForServer(
                        UniqueUserRequest(
                            UserRequest.create(
                                "BTCUSD", Price(target_price=60000.1), Way.up_to
                            )
                        )
                    ),
            ),
            (
                    RequestForServer(
                        UniqueUserRequest(
                            UserRequest.create(
                                "BTCUSDT",
                                PercentOfPoint(target_percent=-3.5, current_price=70000),
                                Way.up_to,
                            )
                        )
                    ),
                    RequestForServer(
                        UniqueUserRequest(
                            UserRequest.create(
                                "EThUSDT",
                                PercentOfPoint(target_percent=-3.5, current_price=70000),
                                Way.up_to,
                            )
                        )
                    ),
            ),
            (
                    UserRequest.create(
                        "BTcuSDt",
                        PercentOfTime(target_percent=20.5, period=Period.v_24h),
                        Way.up_to,
                    ),
                    UserRequest.create(
                        "BTcuSDT",
                        PercentOfTime(target_percent=20.5, period=Period.v_4h),
                        Way.up_to,
                    ),
            ),
        ],
    )
    def test_comparison_requests_different(ex1, ex2):
        assert ex1 != ex2


class TestRequestRepository:
    repo = Repository(sql_db=test_sql)
    dt = datetime.datetime.utcnow()

    user_request1 = UserRequest.create(
        "btcusdt", PercentOfTime(target_percent=23, period=Period.v_24h), Way.up_to
    )
    user_request2 = UserRequest.create(
        "btcusdt", PercentOfTime(target_percent=23, period=Period.v_24h), Way.up_to
    )
    user_request3 = UserRequest.create(
        "btcusdt", PercentOfPoint(target_percent=23, current_price=70000), Way.up_to
    )
    user_request4 = UserRequest.create(
        "ethusdt", PercentOfPoint(target_percent=23, current_price=70000), Way.up_to
    )
    user_request5 = UserRequest.create("btcusdt", Price(target_price=69000), Way.up_to)
    user_request6 = UserRequest.create(
        "btcusdt", Price(target_price=68000), Way.down_to
    )
    user_request7 = UserRequest.create(
        "ETHUsdt", PercentOfTime(target_percent=23, period=Period.v_24h), Way.up_to
    )

    user_1 = User.create(1, "sergey", "ivanov", "sergey_ivanov")
    user_2 = User.create(2, "ivan", "petrov", "ivan_petrov")
    user_3 = User.create(3, "fedor", "sidorov", "fedor_sidorov")

    @pytest.mark.asyncio
    async def test_add(self):
        await self.repo.sql_db.clean()

        user_orm_1 = UserOrm.from_user(self.user_1)
        user_orm_2 = UserOrm.from_user(self.user_2)
        user_orm_3 = UserOrm.from_user(self.user_3)

        await self.repo.add_user(user_orm_1)
        await self.repo.add_user(user_orm_2)
        await self.repo.add_user(user_orm_3)

        self.repo.user_requests = {}
        self.repo.unique_user_requests = {}

        await self.repo.add_request(1, self.user_request1)
        await self.repo.add_request(1, self.user_request2)
        await self.repo.add_request(1, self.user_request3)
        await self.repo.add_request(1, self.user_request4)
        await self.repo.add_request(1, self.user_request5)
        await self.repo.add_request(1, self.user_request6)
        await self.repo.add_request(2, self.user_request2)
        await self.repo.add_request(2, self.user_request4)
        await self.repo.add_request(2, self.user_request5)

        res_user_requests = {
            1: {
                UserRequest.create(
                    "btcusdt",
                    PercentOfTime(target_percent=23, period=Period.v_24h),
                    Way.up_to,
                ),
                UserRequest.create(
                    "btcusdt",
                    PercentOfPoint(target_percent=23, current_price=70000),
                    Way.up_to,
                ),
                UserRequest.create(
                    "ethusdt",
                    PercentOfPoint(target_percent=23, current_price=70000),
                    Way.up_to,
                ),
                UserRequest.create("btcusdt", Price(target_price=69000), Way.up_to),
                UserRequest.create("btcusdt", Price(target_price=68000), Way.down_to),
            },
            2: {
                UserRequest.create(
                    "btcusdt",
                    PercentOfTime(target_percent=23, period=Period.v_24h),
                    Way.up_to,
                ),
                UserRequest.create(
                    "ethusdt",
                    PercentOfPoint(target_percent=23, current_price=70000),
                    Way.up_to,
                ),
                UserRequest.create("btcusdt", Price(target_price=69000), Way.up_to),
            },
        }
        res_unique = {
            UniqueUserRequest(
                UserRequest.create(
                    "btcusdt",
                    PercentOfTime(target_percent=23, period=Period.v_24h),
                    Way.up_to,
                )
            ): {1, 2},
            UniqueUserRequest(
                UserRequest.create(
                    "btcusdt",
                    PercentOfPoint(target_percent=23, current_price=70000),
                    Way.up_to,
                )
            ): {1},
            UniqueUserRequest(
                UserRequest.create(
                    "ethusdt",
                    PercentOfPoint(target_percent=23, current_price=70000),
                    Way.up_to,
                )
            ): {1, 2},
            UniqueUserRequest(
                UserRequest.create("btcusdt", Price(target_price=69000), Way.up_to)
            ): {1, 2},
            UniqueUserRequest(
                UserRequest.create("btcusdt", Price(target_price=68000), Way.down_to)
            ): {1},
        }
        assert self.repo.user_requests == res_user_requests
        assert self.repo.unique_user_requests == res_unique
        assert {r.request_id for r in self.repo.unique_user_requests.keys()} == {
            r.request_id for sets in self.repo.user_requests.values() for r in sets
        }
        assert {  # noqa: F632
                   r.request_id for r in self.repo.unique_user_requests.keys()
               } is not None
        assert {  # noqa: F632
                   r.request_id for sets in self.repo.user_requests.values() for r in sets
               } is not None
        assert (
                await self.repo.get_user_request(1, self.user_request1)
                == self.user_request1
        )
        assert await self.repo.get_user_request(1, self.user_request7) is None
        assert (
                await self.repo.get_all_requests_for_user(2) == res_user_requests[2]
        )
        a1 = await self.repo.get_user_request(1, self.user_request2)
        a2 = await self.repo.get_user_request(2, self.user_request2)
        assert (a1.request_id == a2.request_id)
        a1 = await self.repo.get_user_request(2, self.user_request2)
        a2 = await self.repo.get_user_request(2, self.user_request4)
        assert (a1.request_id != a2.request_id)

        await self.repo.delete_request(1, self.user_request2)  # req2 = req1
        await self.repo.delete_request(1, self.user_request3)
        await self.repo.delete_request(1, self.user_request5)
        await self.repo.delete_request(2, self.user_request2)
        await self.repo.delete_request(2, self.user_request4)
        await self.repo.delete_request(2, self.user_request5)

        res_user_requests_delete = {1: {self.user_request4, self.user_request6}}
        res_unique_delete = {
            UniqueUserRequest(
                UserRequest.create(
                    "ethusdt",
                    PercentOfPoint(target_percent=23, current_price=70000),
                    Way.up_to,
                )
            ): {1},
            UniqueUserRequest(
                UserRequest.create("btcusdt", Price(target_price=68000), Way.down_to)
            ): {1},
        }

        assert self.repo.user_requests == res_user_requests_delete
        assert self.repo.unique_user_requests == res_unique_delete

    @pytest.mark.asyncio
    async def test_get(self):
        assert await self.repo.get_user_request(1, self.user_request4) == self.user_request4

    @pytest.mark.asyncio
    async def test_get_all_requests_for_user_id(self):
        await self.repo.add_request(1, self.user_request1)
        assert len(await self.repo.get_all_requests_for_user(1)) == 3
        await self.repo.delete_request(1, self.user_request1)
        assert len(await self.repo.get_all_requests_for_user(1)) == 2

    @pytest.mark.asyncio
    async def test_get_all_users_for_request(self):
        assert await self.repo.get_all_users_for_request(self.user_request4) == {1}
        await self.repo.add_request(2, self.user_request4)
        await self.repo.add_request(3, self.user_request4)
        assert await self.repo.get_all_users_for_request(self.user_request4) == {1, 2, 3}
        await self.repo.delete_request(2, self.user_request4)
        assert await self.repo.get_all_users_for_request(self.user_request4) == {1, 3}

    @pytest.mark.asyncio
    async def test_delete(self):
        await self.repo.delete_user(1)
        await self.repo.delete_user(2)
        assert len(self.repo.unique_user_requests) == 1
        assert len(self.repo.user_requests) == 1


class TestUserRepository:
    repo = Repository(sql_db=test_sql)
    dt = datetime.datetime.utcnow()

    user_1 = User(
        user_id=1,
        firstname="Anton",
        surname="Petrov",
        username="petrov_a",
        created=dt,
        updated=dt,
    )
    user_2 = User(
        user_id=2,
        firstname="Egor",
        surname="Shkiv",
        username="shkiv_e",
        created=dt,
        updated=dt,
    )
    user_3 = User(
        user_id=3,
        firstname="Andrey",
        surname="Kuper",
        username="kuper_a",
        created=dt,
        updated=dt,
    )
    user_4 = User.create(4, "den", "hooker", "d_h")

    user_orm_1 = UserOrm.from_user(user_1)
    user_orm_2 = UserOrm.from_user(user_2)
    user_orm_3 = UserOrm.from_user(user_3)

    @pytest.mark.asyncio
    async def test_prepare(self):
        await self.repo.sql_db.clean()

    @pytest.mark.asyncio
    async def test_add(self):
        await self.repo.add_user(self.user_1)
        await self.repo.add_user(self.user_2)
        await self.repo.add_user(self.user_3)
        await self.repo.add_user(self.user_4)

        u1 = await self.repo.get_user(1)
        u1_t = self.user_1
        u4 = await self.repo.get_user_from_db(4)
        user_4 = User(**u4.__dict__)
        assert (
                   u1.user_id,
                   u1.firstname,
                   u1.surname,
                   u1.username,
                   u1.ban,
                   u1.created,
                   u1.updated,
               ) == (
                   u1_t.user_id,
                   u1_t.firstname,
                   u1_t.surname,
                   u1_t.username,
                   u1_t.ban,
                   u1_t.created,
                   u1_t.updated,
               )
        assert await self.repo.get_user(2) == User(
            user_id=2,
            firstname="Egor",
            surname="Shkiv",
            username="shkiv_e",
            created=self.dt,
            updated=self.dt,
        )
        assert await self.repo.get_user(3) == User(
            user_id=3,
            firstname="Andrey",
            surname="Kuper",
            username="kuper_a",
            created=self.dt,
            updated=self.dt,
        )
        assert self.repo.users == {
            1: self.user_1,
            2: self.user_2,
            3: self.user_3,
            4: user_4,
        }

    @pytest.mark.asyncio
    async def test_delete_user(self):
        await self.repo.delete_user(1)
        await self.repo.delete_user(4)

        assert self.repo.users == {2: self.user_2, 3: self.user_3}

    @pytest.mark.asyncio
    async def test_update_user(self):
        user = self.user_2
        user.firstname = "Grisha"
        user.surname = "Fuskov"
        user.username = "123"
        user.ban = True
        await self.repo.update_user(user)
        u1 = await self.repo.get_user_from_db(2)
        user_from_db = User(**u1.__dict__)
        assert (user.user_id, user.firstname, user.surname, user.username, user.ban, user.created) == (
            user_from_db.user_id,
            user_from_db.firstname,
            user_from_db.surname,
            user_from_db.username,
            user_from_db.ban,
            user_from_db.created
        )
