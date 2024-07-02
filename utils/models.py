import datetime
import enum
import time

from dataclasses import dataclass, field
from datetime import datetime as dt

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


@dataclass(order=False, eq=False)
class User:
    user_id: int
    name: str
    surname: str
    username: str
    date_registration: datetime.datetime = dt.utcnow()
    date_update: datetime.datetime = dt.utcnow()
    ban: bool = False

    def __eq__(self, other):
        if isinstance(other, User):
            return self.user_id == other.user_id
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.user_id)


@dataclass(repr=False, eq=False, order=False)
class Symbol:
    symbol: str

    def __post_init__(self):
        self.symbol = self.symbol.upper()

    def __repr__(self):
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


@dataclass(frozen=True)
class Percent:
    target_percent: float


@dataclass(frozen=True)
class PercentOfPoint(Percent):
    current_price: float
    weight: int = config.WEIGHT_REQUEST_KLINE

    def to_dict(self):
        return {'type': 'percent_of_point', 'target_percent': self.target_percent, 'current_price': self.current_price}


@dataclass(frozen=True)
class PercentOfTime(Percent):
    period: Period
    weight: int = config.WEIGHT_GET_TICKER

    def to_dict(self):
        return {'type': 'percent_of_time', 'target_percent': self.target_percent, 'period': self.period.value}


@dataclass(frozen=True)
class Price:
    target_price: float
    weight: int = config.WEIGHT_REQUEST_KLINE

    def to_dict(self):
        return {'type': 'price', 'target_price': self.target_price}


@dataclass
class TimeInfo:
    create_time: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    update_time: datetime.datetime = None
    create_time_unix: float = field(default_factory=time.time)
    update_time_unix: float = None

    def __post_init__(self):
        self.update_time = self.create_time
        self.update_time_unix = self.create_time_unix


@dataclass
class BaseRequest:
    request_id: int = field(
        default_factory=lambda: int(time.time() * 100000),
        init=False
    )


@dataclass(eq=False, order=False)
class UserRequest(BaseRequest):
    """
    Класс запросов пользователя.
    Сравнение экземпляров позволяет выявить дубли (время создания и обновления не учитывается).
    """

    symbol: Symbol
    data_request: PercentOfTime | PercentOfPoint | Price
    way: Way
    time_info: TimeInfo = field(default_factory=TimeInfo, init=False)

    def __eq__(self, other):
        if isinstance(other, UserRequest):
            return (self.symbol, self.data_request, self.way) == (other.symbol, other.data_request, other.way)
        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.symbol, self.data_request, self.way))

    def to_dict(self):
        return {
            'id': self.request_id,
            'symbol': self.symbol.symbol,
            'way': self.way.value,
            'data_request': self.data_request.to_dict()
        }

    @classmethod
    def from_dict(cls, data):
        res = None
        data_request = data['data_request']
        if data_request['type'] == 'percent_of_point':
            res = PercentOfPoint(data_request['target_percent'], data_request['current_price'])
        if data_request['type'] == 'percent_of_time':
            res = PercentOfTime(data_request['target_percent'], Period(data_request['period']))
        if data_request['type'] == 'price':
            res = Price(data_request['target_price'])
        return cls(
            symbol=Symbol(data['symbol']),
            data_request=res,
            way=Way(data['way'])
        )


class RequestForServer(BaseRequest):
    """
    В данном классе реализовано сравнение экземпляров запросов,
    которые позволяет сформировать уникальные запросы, поместив их в set().
    """

    def __init__(self, user_request: UserRequest):
        super().__init__()
        self.symbol = user_request.symbol
        self.data_request = user_request.data_request

    def __repr__(self):
        return f'{self.symbol} {self.data_request}'

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

    def to_dict(self):
        return {
            'symbol': self.symbol.symbol,
            'data_request': self.data_request.to_dict()
        }


class BaseResponse:
    pass


class ResponseKline(BaseResponse):
    def __init__(
            self,
            open_time,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            close_time,
            quote_asset_volume,
            number_of_trades,
            taker_buy_base_asset_volume,
            taker_buy_quote_asset_volume
    ):
        """
        Первые 11 элементов списка из ответа сервера по запросу client.get_klines
        """

        self.open_time = open_time
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.close_time = close_time
        self.quote_asset_volume = quote_asset_volume
        self.number_of_trades = number_of_trades
        self.taker_buy_base_asset_volume = taker_buy_base_asset_volume
        self.taker_buy_quote_asset_volume = taker_buy_quote_asset_volume


class ResponseGetTicker(BaseResponse):
    def __init__(self, data_dict: dict):
        """
        Ответ сервера по запросу client.get_ticker
        """

        self.symbol = data_dict['symbol']
        self.price_change = float(data_dict['priceChange'])
        self.price_change_percent = float(data_dict['priceChangePercent'])
        self.weighted_avg_price = float(data_dict['weightedAvgPrice'])
        self.prev_close_price = float(data_dict['prevClosePrice'])
        self.last_price = float(data_dict['lastPrice'])
        self.bid_price = float(data_dict['bidPrice'])
        self.ask_price = float(data_dict['askPrice'])
        self.open_price = float(data_dict['openPrice'])
        self.high_price = float(data_dict['highPrice'])
        self.low_price = float(data_dict['lowPrice'])
        self.volume = float(data_dict['volume'])
        self.open_time = float(data_dict['openTime'])
        self.close_time = float(data_dict['closeTime'])

