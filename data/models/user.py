from pydantic import BaseModel

from typing import Optional, List, Any, Union, Dict

from uuid import uuid4

import os

class AuthToken(BaseModel):
    AccessToken: str
    ExpiresIn: int
    IdToken: str
    NewDeviceMetadata: Optional[Any]
    RefreshToken: str
    TokenType: str

    def __dict__(self):
        yield 'AccessToken', self.AccessToken
        yield 'ExpiresIn', self.ExpiresIn
        yield 'IdToken', self.IdToken
        yield 'NewDeviceMetaData', dict(self.NewDeviceMetadata)
        yield 'RefreshToken', self.RefreshToken
        yield 'TokenType', self.TokenType

class User(BaseModel):
    id: Optional[str] = None

    username: str
    email: str

    confirmed: bool
    auth_token_set: bool = False

    avatar_url: str = os.getenv('AWS_DEFAULT_AVATAR_URL')

    def __iter__(self):
        yield 'id', self.id
        yield 'username', self.username
        yield 'email', self.email
        yield 'confirmed', self.confirmed
        yield 'auth_token_set', self.auth_token_set
        yield 'avatar_url', self.avatar_url

        if self.auth_token_set:
            yield 'auth_token', dict(self.auth_token)

    @staticmethod
    def set_id(user: "User") -> "User":
        user.id = str(uuid4())
        return user

    @staticmethod
    def add_auth_token(user: "User", auth_token: AuthToken):
        user.__setattr__('auth_token', auth_token)
        user.auth_token_set = True
