import json
import logging
import sys

from typing import Annotated
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

import config
from engine import app, repo
from utils.auth import create_access_token, create_refresh_token
from utils.schemas import Token, User, UserRequest

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger("MAIN")


@app.on_event("startup")
async def on_startup():
    pass


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    user = repo.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


@app.get("/users/")
async def get_all_users():
    return repo.get_all_users()


@app.post("/users/", status_code=status.HTTP_201_CREATED, response_model=User)
async def add_user(user: User):
    if user in repo.users:
        raise HTTPException(
            status_code=422, detail=f"User {user.user_id} already exists"
        )
    try:
        repo.add_user(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{add_user.__qualname__} - {e}")


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    if not repo.get_user(user_id):
        raise HTTPException(
            status_code=404, detail=f"User ID {user_id} not found"
        )
    try:
        repo.delete_user(user_id)
        return
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error delete user ID {user_id} - {e}"
        )


@app.put("/users/{user_id}")
async def update_user(user: User):
    try:
        repo.update_user(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{update_user.__qualname__} - {e}")


@app.get("/requests/")
async def get_all_user_requests():
    return repo.get_all_requests()


@app.get("/requests/unique/")
async def get_unique_requests():
    return repo.to_list_unique_user_requests()


@app.get("/requests/server/")
async def get_all_requests_for_server():
    return repo.to_list_unique_requests_for_server()


@app.post("/requests/")
async def add_request(user_id: int, request: UserRequest):
    try:
        repo.add_request(user_id, request)
        return {user_id: request}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'{e}')


@app.get("/requests/{request_id}", response_model=UserRequest)
async def get_request(request_id: UserRequest):
    return repo.get_all_users_for_request(request_id)


@app.delete("/requests/{request_id}")
async def delete_request_for_user(user_id: int, request_id: int):
    repo.delete_request(user_id, request_id)


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    if not (
        form_data.username == config.AUTH_TOKEN
        and form_data.password == config.AUTH_TOKEN
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token()
    refresh_token = create_refresh_token()
    res = Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )
    return res
