import datetime as dt
from pathlib import Path
import json
from typing import Any


class OrdersLoader:
    def __init__(self, json_file: str, indent: int):
        self.json_file = json_file
        self.indent = indent

    def write_order_to_json(
        self,
        item: str,
        quantity: int,
        price: float,
        buyer: str,
        date: dt.date
    ) -> None:
        json_data: dict[str, list[dict[str, Any]]]
        with open(self.json_file, 'r', encoding='utf-8') as f:
            try:
                json_data = json.load(f)
            except json.decoder.JSONDecodeError:
                json_data = {}

        if 'orders' not in json_data:
            json_data['orders'] = []

        json_data['orders'].append(
            dict(
                item=item,
                quantity=quantity,
                price=price,
                buye=buyer,
                date=str(date)
            )
        )

        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=self.indent, ensure_ascii=False)


if __name__ == '__main__':
    BASE_DIR = Path(__file__).resolve().parent
    json_file = str(BASE_DIR) + '/orders.json'
    data: list[dict[str, Any]] = [
        dict(
            item='Медь',
            quantity=100,
            price=400.0,
            buyer='Газпром',
            date=dt.date(2023, 1, 1)
        ),
        dict(
            item='Никель',
            quantity=50,
            price=650.0,
            buyer='Завод имени Баранова',
            date=dt.date(2023, 1, 15)
        ),
        dict(
            item='Платина',
            quantity=1,
            price=1000000.0,
            buyer='Автоваз',
            date=dt.date(2023, 2, 1)
        ),
    ]
    json_loader = OrdersLoader(
        json_file=json_file,
        indent=4
    )
    for row in data:
        json_loader.write_order_to_json(**row)
