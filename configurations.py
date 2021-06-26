import os
from dotenv import load_dotenv

load_dotenv()

hostname = os.getenv('DB_HOST')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DATABASE')
