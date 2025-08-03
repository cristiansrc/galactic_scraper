"""
Configuración centralizada para el producer.
"""
import os
from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB", "galactic_db"),
    "user": os.getenv("POSTGRES_USER", "galactic_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "secret"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

RABBIT_PARAMS = {
    "host": os.getenv("RABBITMQ_HOST", "rabbitmq"),
    "queue": os.getenv("RABBITMQ_QUEUE", "recoleccion_tareas"),
    "user": os.getenv("RABBITMQ_USER", "admin"),
    "password": os.getenv("RABBITMQ_PASSWORD", "admin"),
}

