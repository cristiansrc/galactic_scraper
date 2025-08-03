import os
import json
import time
import uuid
import datetime
import psycopg2
import pika
from dotenv import load_dotenv

print("🌌 Inicializando estación recolectora AGENT-9000...")

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

def get_connection():
    return psycopg2.connect(**DB_PARAMS)

def insert_log(cursor, task_id, message, level="INFO", component="AGENT", details=None):
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

def update_task_status(cursor, task_id, new_status):
    cursor.execute("""
        UPDATE tasks SET status = %s WHERE task_id = %s
    """, (new_status, task_id))

def simulate_recollection(task):
    sku = task["resource_sku"]
    url = task["vendor_planet_url"]

    print(f"🛰️ Desplegando sonda para recolectar: {sku} desde {url}")
    time.sleep(1 + len(sku) % 3)

    if sku == "SKU_NO_ENCONTRADO":
        raise ValueError("❌ SKU no encontrado")
    elif sku == "ERROR_PAGINA_DETALLE":
        raise RuntimeError("❌ Error en página de detalle")
    elif "red-error.com" in url:
        raise ConnectionError("❌ Fallo de red galáctico")

def callback(ch, method, properties, body):
    try:
        task = json.loads(body)
        task_id = task["task_id"]
        sku = task["resource_sku"]
        vendor = task["vendor_planet_url"]

        print(f"\n🔔 Señal entrante: nueva tarea recibida [{task_id}]")
        print(f"🛰️ Desplegando sonda para recolectar: {sku} desde {vendor}")

        with get_connection() as conn:
            with conn.cursor() as cursor:
                # 1️⃣ Marcar como IN_PROGRESS
                cursor.execute("""
                    UPDATE tasks
                    SET status = %s, started_at = %s
                    WHERE task_id = %s
                """, ("IN_PROGRESS", datetime.datetime.now(datetime.timezone.utc), task_id))
                insert_log(cursor, task_id, "Procesamiento iniciado", level="INFO")
                conn.commit()

        # 2️⃣ Simular resultado
        time.sleep(1 + len(sku) % 3)
        result = {"data": f"Resultado ficticio de {sku}"}

        # 3️⃣ Determinar el resultado (éxito o error)
        if "fail_load" in vendor:
            raise Exception("Fallo de red galáctico")
        elif sku == "SKU_NO_ENCONTRADO":
            raise ValueError("SKU no encontrado")
        elif sku == "ERROR_PAGINA_DETALLE":
            raise LookupError("Error en página de detalle")

        # 4️⃣ Éxito: actualizar como DONE
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE tasks
                    SET status = %s, completed_at = %s, extracted_data = %s
                    WHERE task_id = %s
                """, (
                    "DONE",
                    datetime.datetime.now(datetime.timezone.utc),
                    json.dumps(result),
                    task_id
                ))
                insert_log(cursor, task_id, "Recolección completada con éxito", level="INFO", details=result)
                conn.commit()

        print(f"✅ Recolección exitosa de {sku}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"🚨 Error galáctico: ❌ {e}")
        error_type = str(e)

        # 5️⃣ Error: actualizar estado y log
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Determinar estado según tipo de error
                if "red galáctico" in error_type:
                    new_status = "NETWORK_ERROR"
                elif "SKU" in error_type:
                    new_status = "SKU_NOT_FOUND"
                elif "detalle" in error_type:
                    new_status = "DETAIL_PAGE_ERROR"
                else:
                    new_status = "UNKNOWN"

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

                insert_log(cursor, task_id, f"Error durante recolección: {error_type}", level="ERROR", details={"error": error_type})
                conn.commit()

        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    print("🔗 Estableciendo canal cuántico con RabbitMQ...")
    credentials = pika.PlainCredentials(RABBIT_PARAMS["user"], RABBIT_PARAMS["password"])
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_PARAMS["host"], credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=RABBIT_PARAMS["queue"], durable=True)

    print("🛸 AGENT listo para recibir transmisiones. Esperando en la órbita...")
    channel.basic_consume(queue=RABBIT_PARAMS["queue"], on_message_callback=callback)
    channel.start_consuming()

if __name__ == "__main__":
    main()