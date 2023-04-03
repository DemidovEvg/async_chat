from typing import Any, Generic, NewType, Type, TypeVar
import rsa
from pydantic import BaseModel
from pydantic.generics import GenericModel

from . import jim
from .settings import PRIVATE_KEY_PATH, PUBLICK_KEY_PATH


class WrongCommand(Exception):
    pass


Request = NewType('Request', str)
Response = NewType('Response', str)

IncommingMessage = NewType('IncommingMessage', str)

T = TypeVar('T', bound=BaseModel)


class MessageDto(GenericModel, Generic[T]):
    message_model: T | None
    error_message: str | None


def get_message_dto_(schema: Type[T], data: dict[str, Any]) -> MessageDto[T]:
    validator = jim.DataValidator[T](
        schema=schema,
        data=data
    )
    message_dto = MessageDto[T]()
    if not validator.is_valid():
        message_dto.error_message = Request(jim.MessageError(
            response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
            error=str(validator.get_error())
        ).json())
        return message_dto
    message_dto.message_model = validator.get_model()
    return message_dto


def generate_keys():
    if not PUBLICK_KEY_PATH.is_file() or not PRIVATE_KEY_PATH.is_file():
        (publicKey, privateKey) = rsa.newkeys(4096)
        with open(PUBLICK_KEY_PATH, 'wb') as p:
            p.write(publicKey.save_pkcs1('PEM'))
        with open(PRIVATE_KEY_PATH, 'wb') as p:
            p.write(privateKey.save_pkcs1('PEM'))


def load_keys() -> tuple[bytes, bytes]:
    generate_keys()
    with open(PUBLICK_KEY_PATH, 'rb') as p:
        public_key = rsa.PublicKey.load_pkcs1(p.read())
    with open(PRIVATE_KEY_PATH, 'rb') as p:
        private_key = rsa.PrivateKey.load_pkcs1(p.read())
    return private_key, public_key


def encrypt(message: str, key: bytes):
    return rsa.encrypt(message.encode(), key)


def decrypt(ciphertext: bytes, key: bytes):
    try:
        return rsa.decrypt(ciphertext, key).decode()
    except Exception:
        return False
