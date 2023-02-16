
from pathlib import Path
import re
from typing import Pattern
from collections import defaultdict
import csv


class CSVParser:
    def __init__(
            self,
            file_template: str,
            start_num: int,
            headers: list[str],
            result_file: str
    ):
        self.file_template = file_template
        self.start_num = start_num
        self.result_file = result_file
        self.RE_DATA_TEMPLATES = (
            self.get_re_data_templates(headers)
        )
        self.main_data: dict[int, dict[str, str]] = defaultdict(dict)

    def get_re_data_templates(self, headers: list[str]) -> dict[str, Pattern[str]]:
        RE_DATA_TEMPLATES: dict[str, Pattern[str]] = defaultdict()
        for header in headers:
            RE_DATA_TEMPLATES[header] = re.compile(
                r'{header}:\s* (?P<data>.+)'.format(header=header)
            )
        return RE_DATA_TEMPLATES

    def get_file_name(self, num: int) -> str:
        return self.file_template.format(num)

    def fill_data_from_line(self, line: str, file_num: int) -> None:
        for header in self.RE_DATA_TEMPLATES.keys():
            RE_TEMPLATE = self.RE_DATA_TEMPLATES[header]
            result_match = RE_TEMPLATE.search(line)
            if result_match:
                result = result_match.group('data').strip()
                self.main_data[file_num][header] = result

    def get_data(self):
        there_is_another_file = True
        num = self.start_num
        while there_is_another_file:
            try:
                with open(self.get_file_name(num), 'r') as f:
                    for line in f:
                        self.fill_data_from_line(
                            line=line,
                            file_num=num
                        )
                num = num + 1
            except FileNotFoundError:
                there_is_another_file = False

        return self.main_data

    def write_to_csv(self):
        data = list(self.main_data.values())
        headers = data[0].keys()
        with open(self.result_file, 'w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writerows(data)


if __name__ == '__main__':
    BASE_DIR = Path(__file__).resolve().parent
    headers = [
        'Изготивитель системы',
        'Название ОС',
        'Код продукта',
        'Тип системы'
    ]
    parser = CSVParser(
        file_template=str(BASE_DIR) + '/info_{}.txt',
        start_num=1,
        headers=headers,
        result_file=str(BASE_DIR) + '/result.csv',
    )
    data = parser.get_data()
    print(data)
    parser.write_to_csv()
