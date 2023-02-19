from typing import NewType, Any, Generic, TypeVar
from . import jim
from typing import Type
from pydantic import BaseModel
from pydantic.generics import GenericModel


class WrongCommand(Exception):
    pass


Request = NewType('Request', str)
Response = NewType('Response', str)

IncommingMessage = NewType('IncommingMessage', str)
OutgoingMessage = NewType('OutgoingMessage', str)

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
