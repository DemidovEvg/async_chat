"""Декораторы и фукнции аутентификации"""
from typing import Any
import logging
import datetime as dt
from functools import wraps
from jose import JWTError, jwt
from async_chat.server.db import SessionLocal, User
from async_chat.server.user_service import UserService
from async_chat import settings
from async_chat import jim

logger = logging.getLogger('server-logger')


def login_required(func):
    @wraps(func)
    def wrapper(self, data: dict[str, Any], current_user: User | None, *args, **kwargs):
        credentials_exception = False
        if not current_user:
            credentials_exception = True
        if not current_user.is_online():
            credentials_exception = True

        payload = None
        if not credentials_exception:
            token = data.get('token')
            try:
                payload = jwt.decode(
                    token, settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM]
                )
                account_name = payload.get('account_name')
            except JWTError:
                credentials_exception = True

        if credentials_exception or current_user.account_name != account_name:
            error_message = jim.MessageError(
                chain_id=data.get('id'),
                response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                error='Auth required'
            ).json()
            logger.error(
                f'Auth required for data={data} '
            )
            self.put_message_for_current_client(error_message)
            return
        return func(self, data, current_user, *args, **kwargs)
    return wrapper


def append_current_user(func):
    @wraps(func)
    def wrapper(self, data: dict[str, Any], *args, **kwargs):
        account_name: dict[str, str] | None = (
            data.get('user', {}).get('account_name')
        )
        current_user = None
        if account_name:
            with SessionLocal() as session:
                user_service = UserService(session=session)
                current_user = user_service.get_user_by_account_name(
                    account_name=account_name
                )
                if not current_user:
                    error_message = jim.MessageError(
                        chain_id=data.get('id'),
                        response=jim.StatusCodes.HTTP_404_NOT_FOUND,
                        error='User not found'
                    ).json()
                    logger.error(
                        f'User not found for data={data} '
                    )
                    self.put_message_for_current_client(error_message)
                    return
        return func(self, data, current_user, *args, **kwargs)
    return wrapper


def create_access_token(data: dict, expires_delta: dt.timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = dt.datetime.utcnow() + expires_delta
    else:
        expire = dt.datetime.utcnow() + dt.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        claims=to_encode,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt
