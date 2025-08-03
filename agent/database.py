import psycopg2
from psycopg2 import pool

class DatabaseManager:
    def __init__(self, db_uri):
        self.db_uri = db_uri
        self.pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=db_uri)

    def get_connection(self):
        return self.pool.getconn()

    def release_connection(self, conn):
        self.pool.putconn(conn)

    def update_task_status(self, task_id, status):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tasks SET status = %s, updated_at = NOW() WHERE id = %s",
                    (status, task_id)
                )
            conn.commit()
        finally:
            self.release_connection(conn)

    def log_message(self, task_id, status, message):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO execution_logs (task_id, status, log_message) VALUES (%s, %s, %s)",
                    (task_id, status, message)
                )
            conn.commit()
        finally:
            self.release_connection(conn)

    def close(self):
        self.pool.closeall()
