from fastapi import APIRouter, Body, File

from data.models.user import User

from internal.handlers.user_handler import UserHandler

user_router = APIRouter(prefix='/user', tags=['User', 'Auth'])

user_handler = UserHandler()

@user_router.get('/{user_id}')
async def get_user(user_id: str):
    return user_handler.handle_get_user(user_id)

@user_router.get('/by_email/{email}')
async def get_user_by_email(email: str):
    return user_handler.handle_get_user_by_email(email)

@user_router.get('/by_username/{username}')
async def handle_get_user_by_username(username: str):
    return user_handler.handle_get_user_by_username(username)

@user_router.post('/create')
async def create_user(user: User = Body(...)):
    return user_handler.handle_create_user(user)

@user_router.post('/confirm/{user_id}')
async def confirm_user(user_id: str):
    return user_handler.handle_confirm_user(user_id)

@user_router.post('/auth_token/{user_id}')
async def set_auth_token(user_id: str, auth_token: dict = Body(...)):
    return user_handler.handle_set_auth_token(user_id, auth_token)

@user_router.get('/avatar/{user_id}')
async def get_avatar(user_id: str):
    return user_handler.handle_get_avatar(user_id)

@user_router.post('/avatar/{user_id}')
async def set_avatar(user_id: str, file: bytes = File(...)):
    return user_handler.handle_set_avatar(user_id, file)

