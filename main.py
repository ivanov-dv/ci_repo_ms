from fastapi import Request, HTTPException

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
    user = users_repo.get_user(user_id)
    if user is None:
        return {"error": "user not found"}
    return user.to_dict()


@app.get("/get_all_users/")
async def get_all_users():
    users = users_repo.get_all_users()
    return {user_id: user.to_dict() for user_id, user in users.items()}


@app.post("/add_user/")
async def add_user(user: User):
    if user in users_repo.users:
        users_repo.add_user(user)
        return {f"{user.user_id}": f"{user.dict()}"}
    else:
        raise HTTPException(status_code=422, detail="User already exists")

# @app.post("/add_user/")
# async def add_user(data: dict):
#     user = User(data["user_id"], data["name"], data["surname"], data["username"])
#     users_repo.add_user(user)
#     return {f"{user.user_id}": f"{user.to_dict()}"}


@app.delete("/delete_user/{user_id}")
async def delete_user(user_id: int):
    users_repo.delete_user(user_id)
    return {f"{user_id}": "deleted"}


@app.post("/update_user/")
async def update_user(data: dict):
    user = User(data["user_id"], data["firstname"], data["surname"], data["username"], ban=data["ban"])
    users_repo.update_user(user)
    return {f"{data['user_id']}": "updated"}


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
    try:
        user_request = UserRequest.from_dict(data)
        request_repo.add(data['user_id'], user_request)
        return {f"{user_request.request_id}": f"{user_request.to_dict()}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=e)
