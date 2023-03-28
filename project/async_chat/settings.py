import os
from pathlib import Path
from dotenv import load_dotenv


DEFAULT_ROOM = 'common'
BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

database_path = os.environ['database']
PRIVATE_KEY_PATH = BASE_DIR/'publc_key.pem'
PUBLICK_KEY_PATH = BASE_DIR/'private_key.pem'

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
