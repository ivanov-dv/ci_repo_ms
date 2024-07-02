import logging
import pickle

from typing_extensions import Self

from utils.models import *
from utils.patterns import PatternSingleton, RepositoryDB


class UserRepository(RepositoryDB, PatternSingleton):
    users: dict[int, User] = {}

    def add_user(self, user: User):
        self.postgres_db.add_user(
            user.user_id,
            user.name,
            user.surname,
            user.username,
            user.date_registration,
            user.date_update
        )
        self.users[user.user_id] = user

    def delete_user(self, user: User) -> None:
        if self.users.get(user.user_id, None):
            self.postgres_db.delete_user(user.user_id)
            self.users.pop(user.user_id)

    def get_user(self, user_id: int) -> User:
        return self.users.get(user_id, None)

    def get_all_users_id(self) -> set[int]:
        return set(self.users.keys())

    def get_all_users(self) -> set[User]:
        return set(self.users.values())

    def update_user(self, user: User) -> None:
        if self.users.get(user.user_id, None):
            self.postgres_db.update_user(user.user_id, firstname=user.name, surname=user.surname,
                                         username=user.username, ban=user.ban)
            self.users[user.user_id] = user

    def load_users_from_db(self) -> None:
        users = self.postgres_db.get_all_users()
        for user in users:
            self.users[user[0]] = User(user[0], user[1], user[2], user[3], user[4], user[5], user[6])


class RequestRepository(RepositoryDB, PatternSingleton):
    user_requests: dict[int, set[UserRequest]] = {}
    unique_user_requests: dict[UserRequest, set[int]] = {}
    unique_requests_for_server: set[RequestForServer] = set()
    requests_weight: int = 0

    def _delete_unique_user_request(self, user_id: int, request: UserRequest) -> None:
        if request in self.unique_user_requests:
            self.unique_user_requests[request].discard(user_id)
            if not self.unique_user_requests[request]:
                self.unique_user_requests.pop(request, None)

    def _do_unique_requests_for_server(self) -> set[RequestForServer]:
        """
        Создает множество с уникальными запросами (без дублей) на API.

        :return: Set[RequestForServer]
        """

        self.unique_requests_for_server = set()
        self.requests_weight = 0

        for request in self.unique_user_requests.keys():
            if not RequestForServer(request) in self.unique_requests_for_server:
                self.unique_requests_for_server.add(RequestForServer(request))
                self.requests_weight += request.data_request.weight

        return self.unique_requests_for_server

    def add(self, user_id: int, request: UserRequest) -> Self:
        """
        Добавляет запрос пользователя в репозиторий.
        Если запрос уникален, дополнительно добавляет его в список уникальных запросов.
        Если запрос не уникален, меняет id запроса на id уже существующего, чтобы не было дублирования.

        :param user_id: ID пользователя
        :param request: Запрос пользователя
        :return: Экземпляр RequestRepository
        """

        # self._add_in_repo(user_id, request)

        if request in self.unique_user_requests:
            self.unique_user_requests[request].add(user_id)
            list_r = list(self.unique_user_requests.keys())
            i = list_r.index(request)
            id_old_request = list_r[i].request_id
            request.request_id = id_old_request
            self.postgres_db.add_request_to_user(request.request_id, user_id)
        else:
            pickle_dumps = pickle.dumps(self.unique_user_requests)
            self.postgres_db.add_new_request(user_id, request.request_id, pickle_dumps)
            self.unique_user_requests.update({request: {user_id}})

        if user_id in self.user_requests:
            self.user_requests[user_id].add(request)
        else:
            self.user_requests.update({user_id: {request}})

        return self

    def delete(self, user_id: int, request: UserRequest) -> Self:

        if user_id in self.user_requests:
            self.user_requests[user_id].discard(request)
            if not self.user_requests[user_id]:
                self.user_requests.pop(user_id, None)
        self._delete_unique_user_request(user_id, request)

        return self

    def get(self, user_id: int, request: UserRequest) -> UserRequest | None:
        return request if user_id in self.user_requests and request in self.user_requests[user_id] else None

    def get_all_for_user_id(self, user_id: int) -> set[UserRequest] | None:
        return self.user_requests[user_id] if user_id in self.user_requests else None

    def get_all_for_request(self, request: UserRequest) -> set[int] | None:
        return self.unique_user_requests[request] if request in self.unique_user_requests else None

    def update_time_request(self, user_id: int, request: UserRequest) -> Self:
        """
        Обновляет время изменения запроса.
        """

        list_requests = list(self.user_requests[user_id])
        list_requests[list_requests.index(request)].time_info.update_time = dt.utcnow()
        list_requests[list_requests.index(request)].time_info.update_time_unix = time.time()
        self.user_requests[user_id] = set(list_requests)

        return self

    def to_dict_user_requests(self) -> dict:
        res = {}
        for user_id, user_requests in self.user_requests.items():
            reqs = []
            for request in user_requests:
                reqs.append(request.to_dict())
            res.update({user_id: reqs})
        return res

    def to_list_unique_user_requests(self) -> list:
        res = [req.to_dict() for req in self.unique_user_requests.keys()]
        return res

    def to_list_unique_requests_for_server(self) -> list:
        self._do_unique_requests_for_server()
        res = [req.to_dict() for req in self.unique_requests_for_server]
        return res
