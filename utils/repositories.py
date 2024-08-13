from datetime import datetime
from sqlalchemy import update
from typing import Self

from sql.models import UserOrm, UserRequestOrm
from utils.patterns import PatternSingleton, RepositoryDB
from utils.schemas import User, UserRequest, UniqueUserRequest, RequestForServer


class UserRepository(RepositoryDB, PatternSingleton):
    users: dict[int, User] = {}

    def add_user(self, user: User) -> User:
        with self.sql_db.SessionLocal() as session:
            user_orm = UserOrm.from_user(user)
            session.add(user_orm)
            session.commit()
        self.users[user.user_id] = user
        return user

    def delete_user(self, user_id: int) -> User:
        pass

    def get_user(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    def get_all_users(self) -> dict:
        return self.users

    def get_user_from_db(self, user_id: int) -> UserOrm:
        with self.sql_db.SessionLocal() as session:
            user_orm = session.query(UserOrm).filter(UserOrm.user_id == user_id).first()
            return user_orm

    def get_all_users_from_db(self) -> list[UserOrm]:
        with self.sql_db.SessionLocal() as session:
            return session.query(UserOrm).all()

    def update_user(self, user: User) -> User:
        if not self.users.get(user.user_id, None):
            raise Exception(f"Ошибка обновления пользователя (пользователь с id {user.user_id} не существует)")
        with self.sql_db.SessionLocal() as session:
            user.updated = datetime.utcnow()
            stmt = (
                update(UserOrm)
                .values(
                    firstname=user.firstname,
                    surname=user.surname,
                    username=user.username,
                    ban=user.ban,
                    updated=user.updated,
                )
                .filter_by(user_id=user.user_id)
            )
            session.execute(stmt)
            session.commit()
            user_orm = (
                session.query(UserOrm)
                .filter(UserOrm.user_id == user.user_id)
                .first()
            )
            user = User(**user_orm.__dict__)
            self.users[user.user_id] = user
            return user

    def load_users_from_db(self) -> None:
        users = self.get_all_users_from_db()
        for user in users:
            self.users[user.user_id] = User(**user.__dict__)


class RequestRepository(RepositoryDB, PatternSingleton):
    user_requests: dict[int, set[UserRequest]] = {}
    unique_user_requests: dict[UniqueUserRequest, set[int]] = {}
    unique_requests_for_server: set[RequestForServer] = set()
    requests_weight: int = 0

    def _add_request(self, user_id: int, request: UserRequest) -> None:
        with self.sql_db.SessionLocal() as session:
            user_orm = session.query(UserOrm).filter(UserOrm.user_id == user_id).first()
            request_orm = UserRequestOrm.from_user_request(user_orm, request)
            query = self.sql_db.insert_query(
                model=UserRequestOrm,
                values={
                    "request_id": request_orm.request_id,
                    "user_id": request_orm.user_id,
                    "symbol": request_orm.symbol,
                    "request_data": request_orm.request_data,
                    "way": request_orm.way,
                    "created": request_orm.created,
                    "updated": request_orm.updated,
                },
                index_elements=["request_id", "user_id"],
            )
            session.execute(query)
            session.commit()

    def _delete_unique_user_request(self, user_id: int, request: UserRequest) -> None:
        if UniqueUserRequest(request) in self.unique_user_requests:
            self.unique_user_requests[UniqueUserRequest(request)].discard(user_id)
            if not self.unique_user_requests[UniqueUserRequest(request)]:
                self.unique_user_requests.pop(UniqueUserRequest(request), None)

    def _do_unique_requests_for_server(self) -> set[RequestForServer]:
        """
        Создает множество с уникальными запросами (без дублей) на API.

        :return: Set[RequestForServer]
        """

        self.unique_requests_for_server = set()
        self.requests_weight = 0

        for request in self.unique_user_requests.keys():
            if RequestForServer(request) not in self.unique_requests_for_server:
                self.unique_requests_for_server.add(RequestForServer(request))
                self.requests_weight += request.request_data.weight

        return self.unique_requests_for_server

    def add_request(self, user_id: int, request: UserRequest) -> UserRequest:
        """
        Добавляет запрос пользователя в репозиторий.
        Если запрос уникален, дополнительно добавляет его в список уникальных запросов.
        Если запрос не уникален, меняет id запроса на id уже существующего, чтобы не было дублирования.

        :param user_id: Экземпляр пользователя
        :param request: Запрос пользователя
        :return: Экземпляр RequestRepository
        """

        if UniqueUserRequest(request) in self.unique_user_requests:
            self.unique_user_requests[UniqueUserRequest(request)].add(user_id)
            list_r = list(self.unique_user_requests.keys())
            i = list_r.index(UniqueUserRequest(request))
            request.request_id = list_r[i].request_id
            self._add_request(user_id, request)
        else:
            self._add_request(user_id, request)
            self.unique_user_requests.update({UniqueUserRequest(request): {user_id}})

        if user_id in self.user_requests:
            self.user_requests[user_id].add(request)
        else:
            self.user_requests.update({user_id: {request}})
        return request

    def delete_request(self, user_id: int, request_id: int | UserRequest) -> UserRequest:
        """
        Удаляет запрос конкретного пользователя из репозитория и БД.

        :param user_id: Экземпляр пользователя
        :param request_id: Запрос пользователя
        """

        with self.sql_db.SessionLocal() as session:
            if isinstance(request_id, int):
                request_orm = (
                    session.query(UserRequestOrm)
                    .filter(
                        UserRequestOrm.user_id == user_id,
                        UserRequestOrm.request_id == request_id,
                    )
                    .first()
                )
            elif isinstance(request_id, UserRequest):
                request_orm = (
                    session.query(UserRequestOrm)
                    .filter(
                        UserRequestOrm.user_id == user_id,
                        UserRequestOrm.request_id == request_id.request_id,
                    )
                    .first()
                )
            else:
                raise Exception("Invalid request_id")
            session.delete(request_orm)
            session.commit()
            request = UserRequest.from_db(request_orm)
            self.user_requests[user_id].discard(request)
            if not self.user_requests[user_id]:
                self.user_requests.pop(user_id, None)
        self._delete_unique_user_request(user_id, request)
        return request

    def get_user_request(self, user_id: int, request_id: int | UserRequest) -> UserRequest | None:
        with self.sql_db.SessionLocal() as session:
            if isinstance(request_id, int):
                request_orm = (
                    session.query(UserRequestOrm)
                    .filter(
                        UserRequestOrm.user_id == user_id,
                        UserRequestOrm.request_id == request_id,
                    )
                    .first()
                )
                if request_orm:
                    request = UserRequest.from_db(request_orm)
                else:
                    return None
            elif isinstance(request_id, UserRequest):
                request = request_id
            else:
                raise Exception(f"Invalid request_id {request_id}")
        return request if user_id in self.user_requests and request in self.user_requests[user_id] else None

    def get_unique_request(self, request_id: int) -> UserRequest:
        with self.sql_db.SessionLocal() as session:
            request_orm = (
                session.query(UserRequestOrm)
                .filter(
                    UserRequestOrm.request_id == request_id,
                )
                .first()
            )
            print(request_orm)
            request = UserRequest.from_db(request_orm)
        return request

    def get_all_unique_requests(self) -> list[UniqueUserRequest]:
        return list(self.unique_user_requests.keys())

    def get_all_requests_for_user(self, user_id: int) -> set[UserRequest] | None:
        return self.user_requests[user_id] if user_id in self.user_requests else None

    def get_all_users_for_request(self, request_id: int | UserRequest) -> set[int] | None:
        if isinstance(request_id, int):
            request = self.get_unique_request(request_id)
        elif isinstance(request_id, UserRequest):
            request = request_id
        else:
            raise Exception("Invalid request_id")
        u_req = UniqueUserRequest(request)
        return self.unique_user_requests[u_req] if u_req in self.unique_user_requests else None

    def get_all_requests(self) -> dict:
        return self.user_requests

    def get_all_requests_from_db(self) -> list[UserRequestOrm]:
        with self.sql_db.SessionLocal() as session:
            return session.query(UserRequestOrm).all()

    def to_list_unique_user_requests(self) -> list[UniqueUserRequest]:
        return [req for req in self.unique_user_requests]

    def to_list_unique_requests_for_server(self) -> list[RequestForServer]:
        self._do_unique_requests_for_server()
        res = [req for req in self.unique_requests_for_server]
        return res

    def load_requests_from_db(self) -> None:
        requests = self.get_all_requests_from_db()
        for request in requests:
            user_id = request.user_id
            request_user = UserRequest.from_db(request)
            if UniqueUserRequest(request_user) in self.unique_user_requests:
                self.unique_user_requests[UniqueUserRequest(request_user)].add(user_id)
            else:
                self.unique_user_requests.update(
                    {UniqueUserRequest(request_user): {user_id}}
                )
            if user_id in self.user_requests:
                self.user_requests[user_id].add(request_user)
            else:
                self.user_requests.update({user_id: {request_user}})


class Repository(UserRepository, RequestRepository):

    def delete_user(self, user_id: int) -> str:
        user = self.users.get(user_id)
        if not user:
            raise Exception(f"Ошибка удаления пользователя (пользователь с id {user_id} не существует)")
        else:
            user_requests = self.user_requests.get(user_id, [])
            for request in user_requests:
                self._delete_unique_user_request(user_id, request)
            self.user_requests.pop(user_id, None)
            with self.sql_db.SessionLocal() as session:
                user = session.query(UserOrm).filter(UserOrm.user_id == user_id).first()
                if user:
                    session.delete(user)
                    session.commit()
                    self.users.pop(user_id, None)
                return f"User_id {user_id} deleted"

