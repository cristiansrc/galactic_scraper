import psycopg2
import datetime
import uuid
import json

class AgentRepository:
    def __init__(self, db_params):
        self.db_params = db_params

    def get_connection(self):
        return psycopg2.connect(**self.db_params)

    def insert_log(self, task_id, message, level="INFO", component="AGENT", details=None):
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

    def update_task_done(self, task_id, result):
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE tasks
                    SET status = %s, completed_at = %s, extracted_data = %s
                    WHERE task_id = %s
                """, (
                    "COMPLETED",
                    datetime.datetime.now(datetime.timezone.utc),
                    json.dumps(result),
                    task_id
                ))
                conn.commit()

    def update_task_error(self, task_id, new_status, error_type):
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE tasks
                    SET status = %s, completed_at = %s, error_message = %s
                    WHERE task_id = %s
                """, (
                    new_status,
                    datetime.datetime.now(datetime.timezone.utc),
                    error_type,
                    task_id
                ))
                conn.commit()

    def task_exists(self, task_id):
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM tasks WHERE task_id = %s", (task_id,))
                return cursor.fetchone() is not None
