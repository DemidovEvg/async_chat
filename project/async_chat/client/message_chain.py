from collections import UserDict
import datetime as dt
from typing import Hashable
from pydantic import BaseModel


class AutoCleaningDict(UserDict):
    def __init__(self, timeout=180):
        self.timeout = dt.timedelta(seconds=timeout)
        self.timer: dict[Hashable, dt.datetime] = {}
        super().__init__()

    def __delitem__(self, key):
        super().__delitem__(key)

    def __contains__(self, key: object) -> bool:
        self.clean_key(key)
        return super().__contains__(key)

    def __setitem__(self, key, value):
        self.timer[key] = dt.datetime.now()
        super().__setitem__(key, value)

    def __iter__(self):
        for key in list(super().__iter__()):
            self.clean_key(key)
            yield key

    def keys(self):
        self.clean_keys()
        return self.keys()

    def is_key_expired(self, key):
        return dt.datetime.now() - self.timer[key] > self.timeout

    def clean_key(self, key):
        try:
            if (self.is_key_expired(key)):
                super().__delitem__(key)
        except KeyError:
            pass

    def clean_keys(self):
        for key in list(super().keys()):
            self.clean_key(key)

    def __getitem__(self, key):
        self.clean_key(key)
        return super().__getitem__(key)

    def get_data(self):
        for key in list(self.data):
            self.clean_key(key)
        return self.data

    def __repr__(self):
        return f"{type(self).__name__}({self.get_data()})"


messages_chain: dict[str, BaseModel] = AutoCleaningDict()
