from datetime import datetime

from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship

from utils.schemas import UserRequest, User


class Base(DeclarativeBase):
    pass


class UserOrm(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    firstname: Mapped[str] = mapped_column()
    surname: Mapped[str] = mapped_column()
    username: Mapped[str] = mapped_column()
    ban: Mapped[bool] = mapped_column(default=False)
    created: Mapped[datetime] = mapped_column()
    updated: Mapped[datetime] = mapped_column()
    requests: Mapped["UserRequestOrm"] = relationship(cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f'UserOrm(user_id={self.user_id}, firstname="{self.firstname}", surname="{self.surname}", '
            f'username="{self.username}", ban={self.ban}, created={self.created}, updated={self.updated})'
        )

    @staticmethod
    def from_user(user: User):
        return UserOrm(
            user_id=user.user_id,
            firstname=user.firstname,
            surname=user.surname,
            username=user.username,
            ban=user.ban,
            created=user.created,
            updated=user.updated,
        )


class UserRequestOrm(Base):
    __tablename__ = "user_requests"

    request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
                                         )
    symbol: Mapped[str] = mapped_column()
    request_data: Mapped[str] = mapped_column()
    way: Mapped[str] = mapped_column()
    created: Mapped[datetime] = mapped_column()
    updated: Mapped[datetime] = mapped_column()

    def __repr__(self):
        return (
            f"UserRequestOrm(request_id={self.request_id}, user_id={self.user_id}, "
            f'symbol="{self.symbol}", request_data="{self.request_data}", way={self.way})'
        )

    @staticmethod
    def from_user_request(user: UserOrm, request: UserRequest):
        return UserRequestOrm(
            request_id=request.request_id,
            user_id=user.user_id,
            symbol=request.symbol,
            request_data=request.request_data.json(),
            way=request.way.value,
            created=request.created,
            updated=request.updated,
        )

