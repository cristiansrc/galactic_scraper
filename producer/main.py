import json
import uuid
import datetime
import os
import psycopg2
import pika
from dotenv import load_dotenv

print("🌟 Hola desde el producer container")

# ✅ Carga variables desde .env (si lo usamos)
load_dotenv()

# 🎯 Configuración de base de datos y RabbitMQ
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


def get_connection():
    return psycopg2.connect(**DB_PARAMS)

def task_exists(cursor, task_id):
    cursor.execute("SELECT 1 FROM tasks WHERE task_id = %s", (task_id,))
    return cursor.fetchone() is not None

def insert_task(cursor, task):
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


def insert_log(cursor, task_id, message, level="INFO", component="PRODUCER", details=None):
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


def create_tasks():
    skus = [
        "GALACTIC_CRYSTAL_X",
        "VOID_DUST_99",
        "QUANTUM_FLUX_CAPACITOR",
        "SKU_NO_ENCONTRADO",
        "ERROR_PAGINA_DETALLE"
    ]
    urls = [
        "https://vendorA.galactic-market.com",
        "https://vendorB.star-trade.net",
        "https://vendorC.red-error.com/fail_load"
    ]

    tasks = []
    for i in range(5):
        task = {
            "task_id": str(uuid.uuid4()),
            "resource_sku": skus[i],
            "vendor_planet_url": urls[i % len(urls)],
            "priority": (i % 5) + 1,
            "timestamp_created": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        tasks.append(task)
    return tasks


def main():
    try:
        print("🔌 Conectando a PostgreSQL...")
        tasks = create_tasks()
        with get_connection() as conn:
            with conn.cursor() as cursor:
                for task in tasks:
                    if not task_exists(cursor, task["task_id"]):
                        insert_task(cursor, task)
                        insert_log(cursor, task["task_id"], "Tarea registrada en BD como PENDING")
                conn.commit()
        print("✅ Tareas insertadas en BD")

        print("📡 Conectando a RabbitMQ...")
        credentials = pika.PlainCredentials(RABBIT_PARAMS["user"], RABBIT_PARAMS["password"])
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBIT_PARAMS["host"], credentials=credentials))
        channel = connection.channel()
        channel.queue_declare(queue=RABBIT_PARAMS["queue"], durable=True)

        for task in tasks:
            payload = json.dumps(task)

            try:
                channel.basic_publish(
                    exchange="",
                    routing_key=RABBIT_PARAMS["queue"],
                    body=payload,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                print(f"📤 Enviada tarea: {task['task_id']}")

                with get_connection() as conn:
                    with conn.cursor() as cursor:
                        insert_log(cursor, task["task_id"], "Tarea enviada a RabbitMQ", details=task)
                        conn.commit()

            except Exception as e:
                print(f"⚠️ Error al enviar a RabbitMQ: {task['task_id']}")
                insert_log(cursor, task["task_id"], "Error al enviar a RabbitMQ", level="ERROR",
                           details={"error": str(e)})

        connection.close()
        print("✅ Productor finalizó correctamente.")

    except Exception as e:
        print("💥 ERROR FATAL:", e)


if __name__ == "__main__":
    main()