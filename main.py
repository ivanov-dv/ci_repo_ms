from fastapi import Request

from engine import request_repo, app


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
    return {"item_id": "pass"}


@app.get("/get_all_users/")
async def get_all_users():
    return {"item_id": "pass"}


@app.post("/add_user/")
async def add_user(data: dict):
    return {"item_id": "pass"}


@app.delete("/delete_user/{user_id}")
async def delete_user(user_id: int):
    return {"item_id": "pass"}


@app.post("/update_user/{user_id}")
async def update_user(user_id: int, data: dict):
    return {"item_id": "pass"}


@app.get("/user_requests/")
async def get_all_user_requests():
    return request_repo.to_dict_user_requests()


@app.get("/unique_user_requests/")
async def get_all_user_requests():
    return request_repo.to_list_unique_user_requests()


@app.get("/requests_for_server/")
async def get_all_requests_for_server():
    return request_repo.to_list_unique_requests_for_server()


@app.post("/requests/")
async def add_request(data: dict):
    pass
