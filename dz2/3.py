from pathlib import Path
import yaml

from yaml import loader

if __name__ == '__main__':
    BASE_DIR = Path(__file__).resolve().parent
    yaml_file = str(BASE_DIR) + '/data.yaml'

    data = {
        '1А': [1, 2, 3],
        '2Б': 100500,
        '3С': {
            'name': 'Jon',
            'age': 33
        }
    }
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            indent=2
        )

    with open(yaml_file, 'r', encoding='utf-8') as f:
        data_from_yaml = yaml.load(f, loader.FullLoader)

    if yaml.dump(data) == yaml.dump(data_from_yaml):
        print('Данные из файла такие же как и входные')
    else:
        print('Данные в файле другие')
