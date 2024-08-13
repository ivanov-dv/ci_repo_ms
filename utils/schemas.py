import datetime
import enum
import json
import time
from typing import Any

from pydantic import BaseModel, Field


import config


class Period(enum.Enum):
    v_4h = "4h"
    v_8h = "8h"
    v_12h = "12h"
    v_24h = "24h"


class Way(enum.Enum):
    up_to = "up_to"
    down_to = "down_to"
    all = "all"


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    user_id: int
    firstname: str
    surname: str
    username: str
    created: datetime.datetime
    updated: datetime.datetime | None = None
    ban: bool = False

    class Config:
        from_attributes = True

    def __eq__(self, other):
        if isinstance(other, User):
            return self.user_id == other.user_id
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.user_id)

    def __repr__(self):
        return (
            f'User(user_id={self.user_id}, firstname="{self.firstname}", surname="{self.surname}", '
            f'username="{self.username}", ban={self.ban}, created={self.created}, updated={self.updated})'
        )

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def create(user_id, firstname, surname, username):
        dt = datetime.datetime.utcnow()
        return User(
            user_id=user_id,
            firstname=firstname,
            surname=surname,
            username=username,
            created=dt,
            updated=dt,
            ban=False,
        )


class PercentOfPoint(BaseModel):
    target_percent: float
    current_price: float
    weight: int | None = None
    type_request: str = "percent_of_point"

    def model_post_init(self, __context: Any) -> None:
        if not self.weight:
            self.weight = config.WEIGHT_REQUEST_KLINE

    def __repr__(self):
        return (
            f"PercentOfPoint(target_percent={self.target_percent}, current_price={self.current_price}, "
            f'weight={self.weight}, type_request="{self.type_request}")'
        )

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return hash((self.target_percent, self.current_price, self.weight, self.type_request))


class PercentOfTime(BaseModel):
    target_percent: float
    period: Period
    weight: int | None = None
    type_request: str = "percent_of_time"

    def model_post_init(self, __context: Any) -> None:
        if not self.weight:
            self.weight = config.WEIGHT_GET_TICKER

    def __repr__(self):
        return (
            f"PercentOfTime(target_percent={self.target_percent}, period={self.period}, "
            f'weight={self.weight}, type_request="{self.type_request}")'
        )

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return hash((self.target_percent, self.period, self.weight, self.type_request))


class Price(BaseModel):
    target_price: float
    weight: int | None = None
    type_request: str = "price"

    def model_post_init(self, __context: Any) -> None:
        if not self.weight:
            self.weight = config.WEIGHT_REQUEST_KLINE

    def __repr__(self):
        return f'Price(target_price={self.target_price}, weight={self.weight}, type_request="{self.type_request}")'

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return hash((self.target_price, self.weight, self.type_request))


class UserRequest(BaseModel):
    """
    Класс запросов пользователя.
    Сравнение экземпляров позволяет выявить дубли (время создания и обновления не учитывается).
    """

    request_id: int = Field(default_factory=lambda: int(time.time() * 10 ** 9))
    symbol: str
    request_data: PercentOfTime | PercentOfPoint | Price
    way: Way
    created: datetime.datetime
    updated: datetime.datetime

    class Config:
        from_attributes = True

    def model_post_init(self, __context):
        self.symbol = self.symbol.upper()

    def __eq__(self, other):
        if isinstance(other, UserRequest):
            return (self.symbol, self.request_data, self.way) == (
                other.symbol,
                other.request_data,
                other.way,
            )
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.symbol, self.request_data, self.way))

    def __repr__(self):
        return (
            f"UserRequest(request_id={self.request_id}, symbol='{self.symbol}', "
            f"request_data={self.request_data}, way={self.way}, created={self.created}, updated={self.updated})"
        )

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def create(symbol: str, request_data: PercentOfTime | PercentOfPoint | Price, way: Way):
        dt = datetime.datetime.utcnow()
        return UserRequest(symbol=symbol, request_data=request_data, way=way, created=dt, updated=dt)

    @staticmethod
    def from_db(request_orm):
        request_data_temp = json.loads(request_orm.request_data)
        if request_data_temp["type_request"] == "price":
            request_orm.request_data = Price(**request_data_temp)
        elif request_data_temp["type_request"] == "percent_of_point":
            request_orm.request_data = PercentOfPoint(**request_data_temp)
        elif request_data_temp["type_request"] == "percent_of_time":
            request_orm.request_data = PercentOfTime(**request_data_temp)
        else:
            raise ValueError(f"Unknown type request: {request_data_temp}")
        request_orm.way = Way(request_orm.way)
        request_orm.__dict__.pop("_sa_instance_state")
        return UserRequest(**request_orm.__dict__)


class UserRequestSchema(BaseModel):
    symbol: str
    request_data: PercentOfTime | PercentOfPoint | Price
    way: Way
    created: datetime.datetime
    updated: datetime.datetime


class UniqueUserRequest(BaseModel):
    request_id: int | None = None
    symbol: str | None = None
    way: Way | None = None
    request_data: PercentOfTime | PercentOfPoint | Price | None = None

    class Config:
        from_attributes = True

    def __init__(self, request: UserRequest):
        super().__init__()
        self.request_id = request.request_id
        self.symbol = request.symbol
        self.way = request.way
        self.request_data = request.request_data

    def __eq__(self, other):
        if isinstance(other, UniqueUserRequest):
            return (self.symbol, self.request_data, self.way) == (
                other.symbol,
                other.request_data,
                other.way,
            )
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.symbol, self.request_data, self.way))

    def __repr__(self):
        return (
            f'UniqueUserRequest(request_id={self.request_id}, symbol="{self.symbol}", '
            f'way="{self.way}", request_data={self.request_data})'
        )

    def __str__(self):
        return self.__repr__()


class RequestForServer(BaseModel):
    symbol: str | None = None
    request_data: PercentOfTime | PercentOfPoint | Price | None = None

    class Config:
        from_attributes = True

    def __init__(self, request: UniqueUserRequest | UserRequest):
        super().__init__()
        self.symbol = request.symbol
        self.request_data = request.request_data

    def __eq__(self, other):
        if isinstance(other, RequestForServer):
            if isinstance(self.request_data, PercentOfTime) and isinstance(
                    other.request_data, PercentOfTime
            ):
                return (self.symbol, self.request_data.period) == (
                    other.symbol,
                    other.request_data.period,
                )
            if isinstance(self.request_data, (Price, PercentOfPoint)) and isinstance(
                    other.request_data, (Price, PercentOfPoint)
            ):
                return self.symbol == other.symbol
            return (self.symbol, self.request_data) == (
                other.symbol,
                other.request_data,
            )
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.symbol)

    def __repr__(self):
        return f'RequestForServer(symbol="{self.symbol}", request_data={self.request_data})'

    def __str__(self):
        return self.__repr__()
