import psycopg2
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_uri):
        self.db_uri = db_uri

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(self.db_uri)
        try:
            yield conn
        finally:
            conn.close()

    def insert_task(self, data):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tasks (data) VALUES (%s) RETURNING id;",
                    (data,)
                )
                task_id = cur.fetchone()[0]
                conn.commit()
                return task_id

    def insert_log(self, task_id, message):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO logs (task_id, message) VALUES (%s, %s);",
                    (task_id, message)
                )
                conn.commit()
