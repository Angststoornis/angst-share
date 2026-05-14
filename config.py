import os
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = "uploads"
DB_PATH = "instances/files.db"
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1 GB
SECRET_KEY = os.getenv("SECRET_KEY", "supergeheime-angst-key-change-me")