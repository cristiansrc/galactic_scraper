import json
import uuid
import datetime
import os
import sys
from dotenv import load_dotenv
import logging

from repository import TaskRepository
from messaging import RabbitMQProducer
from service import TaskService
from config import DB_PARAMS, RABBIT_PARAMS

# ✅ Carga variables desde .env (si lo usamos)
load_dotenv()

def create_tasks() -> list[dict]:
    """Genera una lista de tareas de ejemplo."""
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


def main() -> None:
    """Punto de entrada principal del producer."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    logging.info("🌟 Iniciando producer container")
    try:
        repository = TaskRepository(DB_PARAMS)
        producer = RabbitMQProducer(RABBIT_PARAMS)
        service = TaskService(repository, producer)

        tasks = create_tasks()
        service.process_tasks(tasks)
        logging.info("✅ Tareas procesadas e insertadas en BD y RabbitMQ")
    except Exception as e:
        logging.exception(f"💥 Error fatal en producer: {e}")
    finally:
        try:
            producer.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()