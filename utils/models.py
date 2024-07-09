import datetime
import enum
import time

from datetime import datetime as dt
from pydantic import BaseModel, ConfigDict, Field

import config


class Period(enum.Enum):
    v_4h = '4h'
    v_8h = '8h'
    v_12h = '12h'
    v_24h = '24h'


class TypeRequest(enum.Enum):
    period = 'period'
    price = 'price'


class Way(enum.Enum):
    up_to = 'up_to'
    down_to = 'down_to'
    all = 'all'


class TimeInfo(BaseModel):
    create_time: datetime.datetime = dt.utcnow()
    update_time: datetime.datetime = None
    create_time_unix: float = time.time()
    update_time_unix: float = None

    def __init__(self):
        super(TimeInfo, self).__init__()
        self.update_time = self.create_time
        self.update_time_unix = self.create_time_unix


class User(BaseModel):
    user_id: int
    firstname: str
    surname: str
    username: str
    time_info: TimeInfo = Field(default_factory=TimeInfo)
    ban: bool = False

    def __init__(self, user_id: int, firstname: str, surname: str, username: str,
                 time_info: TimeInfo, ban: bool = False):
        super(User, self).__init__(user_id=user_id, firstname=firstname, surname=surname, username=username)
        self.time_info = time_info
        self.ban = ban

    def __eq__(self, other):
        if isinstance(other, User):
            return self.user_id == other.user_id
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.user_id)

    @classmethod
    def load_user(cls, data):
        time_info = TimeInfo()
        time_info.create_time = data[4]
        time_info.update_time = data[5]
        time_info.create_time_unix = data[6]
        time_info.update_time_unix = data[7]
        return cls(data[0], data[1], data[2], data[3], time_info, data[8])


class Symbol(BaseModel):
    symbol: str

    def __init__(self, symbol: str):
        super(Symbol, self).__init__(symbol=symbol.upper())

    def __repr__(self):
        return f'Symbol(\'{self.symbol}\')'

    def __str__(self):
        return self.symbol

    def __eq__(self, other):
        if isinstance(other, Symbol):
            return self.symbol == other.symbol
        if isinstance(other, str):
            return self.symbol == other

    def __ne__(self, other):
        if isinstance(other, Symbol):
            return self.symbol != other.symbol
        if isinstance(other, str):
            return self.symbol != other

    def __hash__(self):
        return hash(self.symbol)


class PercentOfPoint(BaseModel):
    target_percent: float
    current_price: float
    weight: int = config.WEIGHT_REQUEST_KLINE

    model_config = ConfigDict(frozen=True)

    def __init__(self, target_percent: float, current_price: float):
        super(PercentOfPoint, self).__init__(target_percent=target_percent, current_price=current_price)


class PercentOfTime(BaseModel):
    target_percent: float
    period: Period
    weight: int = config.WEIGHT_GET_TICKER

    model_config = ConfigDict(frozen=True)

    def __init__(self, target_percent: float, period: Period):
        super(PercentOfTime, self).__init__(target_percent=target_percent, period=period)


class Price(BaseModel):
    target_price: float
    weight: int = config.WEIGHT_REQUEST_KLINE

    model_config = ConfigDict(frozen=True)

    def __init__(self, target_price: float):
        super(Price, self).__init__(target_price=target_price)


class UserRequest(BaseModel):
    """
    Класс запросов пользователя.
    Сравнение экземпляров позволяет выявить дубли (время создания и обновления не учитывается).
    """

    request_id: int = Field(default_factory=lambda: int(time.time() * 10**9))
    symbol: Symbol
    data_request: PercentOfTime | PercentOfPoint | Price
    way: Way
    time_info: TimeInfo = Field(default_factory=TimeInfo)

    def __init__(self, symbol: Symbol, data_request: PercentOfTime | PercentOfPoint | Price, way: Way):
        super(UserRequest, self).__init__(symbol=symbol, data_request=data_request, way=way)

    def __eq__(self, other):
        if isinstance(other, UserRequest):
            return (self.symbol, self.data_request, self.way) == (other.symbol, other.data_request, other.way)
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.symbol, self.data_request, self.way))


class UniqueUserRequest(BaseModel):
    request_id: int
    symbol: Symbol
    data_request: PercentOfTime | PercentOfPoint | Price
    way: Way

    def __init__(self, user_request: UserRequest):
        super(UniqueUserRequest, self).__init__(request_id=user_request.request_id, symbol=user_request.symbol,
                                                data_request=user_request.data_request, way=user_request.way)

    def __eq__(self, other):
        if isinstance(other, UniqueUserRequest):
            return ((self.symbol, self.data_request, self.way) ==
                    (other.symbol, other.data_request, other.way))
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.symbol, self.data_request, self.way))


class RequestForServer(BaseModel):
    symbol: Symbol
    data_request: PercentOfTime | PercentOfPoint | Price

    def __init__(self, user_request: UniqueUserRequest):
        super(RequestForServer, self).__init__(symbol=user_request.symbol, data_request=user_request.data_request)

    def __eq__(self, other):
        if isinstance(other, RequestForServer):
            if isinstance(self.data_request, PercentOfTime) and isinstance(other.data_request, PercentOfTime):
                return (self.symbol, self.data_request.period) == (other.symbol, other.data_request.period)
            if (isinstance(self.data_request, (Price, PercentOfPoint)) and
                    isinstance(other.data_request, (Price, PercentOfPoint))):
                return self.symbol == other.symbol
            return (self.symbol, self.data_request) == (other.symbol, other.data_request)
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.symbol)
