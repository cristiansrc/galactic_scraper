import psycopg2
import datetime
import uuid
import json
import logging
from typing import Any, Dict

class TaskRepository:
    """
    Repositorio para operaciones de base de datos relacionadas con tareas y logs.
    """
    def __init__(self, db_params: dict):
        self.db_params = db_params

    def get_connection(self) -> psycopg2.extensions.connection:
        return psycopg2.connect(**self.db_params)

    def task_exists(self, task_id: str) -> bool:
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM tasks WHERE task_id = %s", (task_id,))
                exists = cursor.fetchone() is not None
                logging.debug(f"Verificando existencia de tarea {task_id}: {exists}")
                return exists

    def insert_task(self, task: Dict[str, Any]) -> None:
        # Validación básica
        required_fields = ["task_id", "resource_sku", "vendor_planet_url", "priority", "timestamp_created"]
        for field in required_fields:
            if field not in task:
                raise ValueError(f"Falta el campo requerido: {field}")
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tasks (task_id, resource_sku, vendor_planet_url, priority, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    task["task_id"],
                    task["resource_sku"],
                    task["vendor_planet_url"],
                    task["priority"],
                    "PENDING",
                    task["timestamp_created"]
                ))
                conn.commit()
                logging.info(f"Tarea insertada en BD: {task['task_id']}")

    def insert_log(self, task_id: str, message: str, level: str = "INFO", component: str = "PRODUCER", details: Any = None) -> None:
        """
        Inserta un log relacionado a una tarea en la base de datos.
        Args:
            task_id: ID de la tarea relacionada.
            message: Mensaje del log.
            level: Nivel del log (INFO, WARNING, ERROR).
            component: Componente que genera el log.
            details: Información adicional en formato JSON serializable.
        """
        if not task_id or not message:
            raise ValueError("task_id y message son obligatorios para el log.")
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO task_logs (log_id, task_id, timestamp, level, message, component, details)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()),
                        task_id,
                        datetime.datetime.now(datetime.timezone.utc),
                        level,
                        message,
                        component,
                        json.dumps(details) if details else None
                    ))
                    conn.commit()
                    logging.debug(f"Log insertado para tarea {task_id}: {message}")
        except Exception as e:
            logging.error(f"Error al insertar log para tarea {task_id}: {e}")
            raise
