from typing import Any, Generic, TypeVar, Type
import pydantic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class DataValidator(Generic[T]):
    def __init__(self, schema: Type[T], data: dict[str, Any]):
        self.schema = schema
        self.data = data
        self._is_valid: bool | None = None
        self._error_data: str | None = None

    def is_valid(self) -> bool:
        if self._is_valid is not None:
            return self._is_valid
        try:
            self._model: T = self.schema(**self.data)
            return True
        except pydantic.error_wrappers.ValidationError as exc:
            self._error_data = str(exc.errors())
            return False

    def get_error(self) -> str | None:
        return self._error_data

    def get_model(self) -> T:
        if not hasattr(self, '_model'):
            raise AttributeError('Please validate before get_model')
        return self._model
