import os
from pathlib import Path
from dotenv import load_dotenv


DEFAULT_ROOM = 'common'
BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

database_path = os.environ['database']

