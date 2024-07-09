import pickle

from typing_extensions import Self

from utils.models import *
from utils.patterns import PatternSingleton, RepositoryDB


class UserRepository(RepositoryDB, PatternSingleton):
    users: dict[int, User] = {}

    def add_user(self, user: User):
        self.postgres_db.add_user(
            user.user_id,
            user.firstname,
            user.surname,
            user.username,
            user.time_info
        )
        self.users[user.user_id] = user

    def delete_user(self, user_id: int) -> None:
        if self.users.get(user_id, None):
            self.postgres_db.delete_user(user_id)
            self.users.pop(user_id)

    def get_user(self, user_id: int) -> User:
        return self.users.get(user_id, None)

    def get_all_users_id(self) -> set[int]:
        return set(self.users.keys())

    def get_all_users(self) -> dict[int, User]:
        return self.users

    def update_user(self, user: User) -> None:
        if self.users.get(user.user_id, None):
            self.postgres_db.update_user(
                user.user_id, firstname=user.firstname, surname=user.surname,username=user.username,
                ban=user.ban, date_update=dt.utcnow(), time_update_unix=time.time()
            )
            self.users[user.user_id] = user

    def load_users_from_db(self) -> None:
        users = self.postgres_db.get_all_users()
        for user in users:
            self.users[user[0]] = User.load_user(user)


class RequestRepository(RepositoryDB, PatternSingleton):
    user_requests: dict[int, set[UserRequest]] = {}
    unique_user_requests: dict[UniqueUserRequest, set[int]] = {}
    unique_requests_for_server: set[RequestForServer] = set()
    requests_weight: int = 0

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

        if UniqueUserRequest(request) in self.unique_user_requests:
            self.unique_user_requests[UniqueUserRequest(request)].add(user_id)
            list_r = list(self.unique_user_requests.keys())
            i = list_r.index(UniqueUserRequest(request))
            id_old_request = list_r[i].request_id
            request.request_id = id_old_request
            pickle_dumps = pickle.dumps(request)
            self.postgres_db.add_new_request(user_id, request.request_id, pickle_dumps)
        else:
            pickle_dumps = pickle.dumps(request)
            self.postgres_db.add_new_request(user_id, request.request_id, pickle_dumps)
            self.unique_user_requests.update({UniqueUserRequest(request): {user_id}})

        if user_id in self.user_requests:
            self.user_requests[user_id].add(request)
        else:
            self.user_requests.update({user_id: {request}})

        return self

    def delete(self, user_id: int, request: UserRequest) -> Self:
        """
        Удаляет запрос конкретного пользователя из репозитория и БД.

        :param user_id: ID пользователя
        :param request: Запрос пользователя
        """

        if user_id in self.user_requests:
            self.postgres_db.delete_request_for_user(user_id, request.request_id)
            self.user_requests[user_id].discard(request)
            if not self.user_requests[user_id]:
                self.user_requests.pop(user_id, None)
        self._delete_unique_user_request(user_id, request)

        return self

    def get(self, user_id: int, request: UserRequest) -> UserRequest | None:
        return request if user_id in self.user_requests and request in self.user_requests[user_id] else None

    def get_all_requests_for_user_id(self, user_id: int) -> set[UserRequest] | None:
        return self.user_requests[user_id] if user_id in self.user_requests else None

    def get_all_users_for_request(self, request: UserRequest) -> set[int] | None:
        u_req = UniqueUserRequest(request)
        return self.unique_user_requests[u_req] if u_req in self.unique_user_requests else None

    def update_time_request(self, user_id: int, request: UserRequest) -> Self:
        """
        Обновляет время изменения запроса.
        """

        list_requests = list(self.user_requests[user_id])
        list_requests[list_requests.index(request)].time_info.update_time = dt.utcnow()
        list_requests[list_requests.index(request)].time_info.update_time_unix = time.time()
        self.user_requests[user_id] = set(list_requests)

        return self

    def to_list_unique_user_requests(self) -> list:
        res = [req.dict(users) for req, users in self.unique_user_requests.items()]
        return res

    def to_list_unique_requests_for_server(self) -> list:
        self._do_unique_requests_for_server()
        res = [req.dict() for req in self.unique_requests_for_server]
        return res

    def load_requests_from_db(self) -> None:
        all_requests = self.postgres_db.get_all_requests()
        for r_data in all_requests:
            request_id, request, user_id = r_data[0], pickle.loads(r_data[1]), r_data[2]
            if request in self.unique_user_requests:
                self.unique_user_requests[UniqueUserRequest(request)].add(user_id)
            else:
                self.unique_user_requests.update({UniqueUserRequest(request): {user_id}})

            if user_id in self.user_requests:
                self.user_requests[user_id].add(request)
            else:
                self.user_requests.update({user_id: {request}})
