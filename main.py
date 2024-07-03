from fastapi import Request

from engine import request_repo, users_repo, app
from utils.models import User, UserRequest


@app.middleware("http")
async def check_user(request: Request, call_next):
    """
    Middleware for checking client IP address.
    """
    if request.client.host == '127.0.0.1':
        response = await call_next(request)
        return response


@app.get("/get_user/{user_id}")
async def get_user(user_id: int):
    user = users_repo.get_user(user_id).to_dict()
    if user is None:
        return {"error": "user not found"}
    return user


@app.get("/get_all_users/")
async def get_all_users():
    users = users_repo.get_all_users()
    return {user_id: user.to_dict() for user_id, user in users}


@app.post("/add_user/")
async def add_user(data: dict):
    user = User(data["user_id"], data["name"], data["surname"], data["username"])
    users_repo.add_user(user)
    return {f"{user.user_id}": f"{user.to_dict()}"}


@app.delete("/delete_user/{user_id}")
async def delete_user(user_id: int):
    users_repo.delete_user(user_id)
    return {f"{user_id}": "deleted"}


@app.post("/update_user/{user_id}")
async def update_user(user_id: int, data: dict):
    user = User(data["user_id"], data["name"], data["surname"], data["username"])
    users_repo.update_user(user)
    return {f"{user_id}": "updated"}


@app.get("/user_requests/")
async def get_all_user_requests():
    return request_repo.to_dict_user_requests()


@app.get("/unique_user_requests/")
async def get_all_user_requests():
    return request_repo.to_list_unique_user_requests()


@app.get("/requests_for_server/")
async def get_all_requests_for_server():
    return request_repo.to_list_unique_requests_for_server()


@app.post("/add_request/")
async def add_request(data: dict):
    user_request = UserRequest.from_dict(data)
    return {f"{user_request.request_id}": f"{user_request.to_dict()}"}
