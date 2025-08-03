import os
from dotenv import load_dotenv

load_dotenv()

def get_database_uri():
    return os.getenv("DATABASE_URL")

def get_rabbitmq_uri():
    return os.getenv("RABBITMQ_URL")
