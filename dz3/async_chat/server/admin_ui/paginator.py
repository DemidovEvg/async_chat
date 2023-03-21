from typing import Callable
import math


class Paginator:
    def __init__(self, items: list[object], page_size: int = 5):
        self.size = page_size
        self.page = 1
        self.items_origin = items
        self.items = items
        self.filter_ = None

    @property
    def current_page_num(self) -> int:
        return self.page

    def reload_items(self, items: list[object]) -> None:
        self.items_origin = items
        self.items = items
        if self.filter_:
            self.apply_filter(self.filter_)

    def apply_filter(self, filter: Callable[[], None]) -> None:
        self.items = filter(self.items)

    def reset_filter(self) -> None:
        self.items = self.items_origin

    def is_it_first_page(self) -> bool:
        return self.page == 1

    def is_it_last_page(self) -> bool:
        if len(self.items) == 0:
            return True

        max_page = math.ceil(len(self.items) / self.size)
        return self.page >= max_page

    def set_page(self, page: int):
        self.page = page

    def get_page(self, page: int) -> list[object]:
        self.set_page(page)
        return self.get_curent_page()

    def get_curent_page(self) -> list[object]:
        return self.items[(self.page - 1)*self.size: self.page*self.size-1]

    def get_next(self) -> list[object]:
        self.set_page(self.page + 1)
        return self.get_curent_page()

    def get_previous(self) -> list[object]:
        self.set_page(self.page - 1)
        return self.get_curent_page()
