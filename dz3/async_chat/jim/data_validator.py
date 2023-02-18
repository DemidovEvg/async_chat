from typing import Any, Generic, TypeVar
import pydantic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class DataValidator(Generic[T]):
    def __init__(self, schema: T, data: dict[str, Any]):
        self.schema = schema
        self.data = data
        self.__model: T | None = None
        self.__is_valid: bool | None = None
        self.__error_data: str | None = None

    def is_valid(self) -> bool:
        if self.__is_valid is not None:
            return self.__is_valid
        try:
            self.__model: T = self.schema(**self.data)
            return True
        except pydantic.error_wrappers.ValidationError as exc:
            self.__error_data = str(exc.errors())
            return False

    def get_error(self) -> str:
        return self.__error_data

    def get_model(self) -> T:
        return self.__model
