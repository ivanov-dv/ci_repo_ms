import logging
import sys

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

import config

from engine import app, repo
from utils.auth import create_access_token, create_refresh_token
from utils.schemas import Token, User, UserRequest, UserRequestSchema


@app.get('/users/{user_id}', response_model=User)
async def get_user(user_id: int):
    try:
        user = await repo.get_user(user_id)
    except Exception as e:
        logging.error(f'get_user error: {e}')
        raise HTTPException(status_code=500, detail=f'get_user error: {e}')
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


@app.get('/users/')
async def get_all_users():
    try:
        res = await repo.get_all_users()
        return res
    except Exception as e:
        logging.error(f'get_all_users error: {e}')
        raise HTTPException(status_code=500, detail=f'get_all_users error: {e}')


@app.post('/users/', status_code=status.HTTP_201_CREATED, response_model=User)
async def add_user(user: User):
    if user in repo.users:
        raise HTTPException(
            status_code=422, detail=f'User {user.user_id} already exists'
        )
    try:
        await repo.add_user(user)
        return user
    except Exception as e:
        logging.error(f'add_user error: {e}')
        raise HTTPException(status_code=400, detail=f'add_user error: {e}')


@app.delete('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    if not await repo.get_user(user_id):
        raise HTTPException(
            status_code=404, detail=f'User ID {user_id} not found'
        )
    try:
        await repo.delete_user(user_id)
    except Exception as e:
        logging.error(f'delete_user error: {e}')
        raise HTTPException(
            status_code=400, detail=f'Error delete user ID {user_id} - {e}'
        )


@app.put('/users/{user_id}')
async def update_user(user: User):
    try:
        await repo.update_user(user)
        return user
    except Exception as e:
        logging.error(f'update_user error: {e}')
        raise HTTPException(status_code=400, detail=f'update_user error: {e}')


@app.get("/requests/{request_id}", response_model=UserRequest)
async def get_request(request_id: int):
    try:
        return await repo.get_unique_request(request_id)
    except Exception as e:
        logging.error(f'get_request error: {e}')
        raise HTTPException(status_code=500, detail=f'get_request error: {e}')


@app.get('/requests/')
async def get_all_user_requests():
    try:
        res = await repo.get_all_requests()
        return res
    except Exception as e:
        logging.error(f'get_all_user_requests error: {e}')
        raise HTTPException(status_code=500, detail=f'get_all_user_requests error: {e}')


@app.get('/users/requests/{request_id}')
async def get_all_users_for_request(request_id: int):
    try:
        res = await repo.get_all_users_for_request(request_id)
        return res
    except Exception as e:
        logging.error(f'get_all_users_for_request error: {e}')
        raise HTTPException(status_code=500, detail=f'get_all_users_for_request error: {e}')


@app.get('/requests/users/{user_id}')
async def get_all_requests_for_user(user_id: int):
    try:
        return await repo.get_all_requests_for_user(user_id)
    except Exception as e:
        logging.error(f'get_all_requests_for_user error: {e}')
        raise HTTPException(status_code=500, detail=f'get_all_requests_for_user error: {e}')


@app.get('/requests/unique/')
async def get_unique_requests():
    try:
        return await repo.to_list_unique_user_requests()
    except Exception as e:
        logging.error(f'get_unique_requests error: {e}')
        raise HTTPException(status_code=500, detail=f'get_unique_requests error: {e}')


@app.get('/requests/server/')
async def get_requests_for_server():
    try:
        return await repo.to_list_unique_requests_for_server()
    except Exception as e:
        logging.error(f'get_all_requests_for_server error: {e}')
        raise HTTPException(status_code=500, detail=f'get_requests_for_server error: {e}')


@app.post('/requests/', status_code=status.HTTP_201_CREATED)
async def add_request(user_id: int, request: UserRequestSchema):
    request = UserRequest(**request.dict())
    try:
        await repo.add_request(user_id, request)
        return {user_id: request}
    except Exception as e:
        logging.error(f'add_request error: {e}')
        raise HTTPException(status_code=500, detail=f'add_request error: {e}')


@app.delete('/requests/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_request_for_user(user_id: int, request_id: int):
    if not await repo.get_user_request(user_id, request_id):
        raise HTTPException(
            status_code=404, detail=f'Request ID {request_id} for user ID {user_id} not found'
        )
    try:
        await repo.delete_request(user_id, request_id)
    except Exception as e:
        logging.error(f'delete_request_for_user error: {e}')
        raise HTTPException(
            status_code=500, detail=f'Error delete request ID {request_id} for user ID {user_id} - {e}'
        )


@app.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    if not (form_data.username == config.AUTH_TOKEN and form_data.password == config.AUTH_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token()
    refresh_token = create_refresh_token()
    token = Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
    return token


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level='info')
