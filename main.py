import logging
import sys

from fastapi import Request, HTTPException, status

from engine import request_repo, users_repo, app
from utils.models import User, UserRequest


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
l_1 = logging.getLogger('MAIN')


@app.middleware("http")
async def check_user(request: Request, call_next):
    """
    Middleware for checking client IP address.
    """
    if request.client.host == '127.0.0.1':
        response = await call_next(request)
        return response


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    user = users_repo.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f'User {user_id} not found')
    return user


@app.get("/users/")
async def get_all_users():
    users = users_repo.get_all_users()
    return [user for user in users.values()]


@app.post("/users/", status_code=status.HTTP_201_CREATED, response_model=User)
async def add_user(user: User):
    if user not in users_repo.users:
        raise HTTPException(status_code=422, detail=f"User {user.user_id} already exists")
    try:
        users_repo.add_user(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'{add_user.__qualname__} - {e}')


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    if not users_repo.get_user(user_id):
        raise HTTPException(status_code=404, detail=f"Order with ID {user_id} not found")
    try:
        users_repo.delete_user(user_id)
        return
    except Exception as e:
        l_1.error(f'{delete_user.__qualname__} - {e}')
        raise HTTPException(status_code=400, detail=f'Error delete user with ID {user_id}')



@app.put("/users/{user_id}")
async def update_user(data: dict):
    user = User(data["user_id"], data["firstname"], data["surname"], data["username"], ban=data["ban"])
    users_repo.update_user(user)
    return {f"{data['user_id']}": "updated"}


@app.get("/requests/user/")
async def get_all_user_requests():
    return request_repo.to_dict_user_requests()


@app.get("/requests/unique/")
async def get_all_user_requests():
    return request_repo.to_list_unique_user_requests()


@app.get("/requests/server/")
async def get_all_requests_for_server():
    return request_repo.to_list_unique_requests_for_server()


@app.post("/requests/")
async def add_request(data: dict):
    try:
        user_request = UserRequest.from_dict(data)
        request_repo.add(data['user_id'], user_request)
        return {f"{user_request.request_id}": f"{user_request.to_dict()}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=e)


@app.get("/requests/{request_id}")
async def get_request(user_id: int, request_id: int):
    request = request_repo.get(user_id, request_id)
    return request


@app.delete("/requests/{request_id}")
async def delete_request(user_id: int, request_id: int):
    request_repo.delete(user_id, request_id)
