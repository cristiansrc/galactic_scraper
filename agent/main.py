import logging
import os
from dotenv import load_dotenv
from repository import AgentRepository
from messaging import RabbitMQConsumer
from service import AgentService
from config import DB_PARAMS, RABBIT_PARAMS

def main() -> None:
    """Punto de entrada principal del agent."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    logging.info("🌌 Inicializando estación recolectora AGENT-9000...")
    consumer = None
    try:
        repository = AgentRepository(DB_PARAMS)
        service = AgentService(repository)
        consumer = RabbitMQConsumer(RABBIT_PARAMS)

        def on_message(ch, method, properties, body):
            service.handle_message(ch, method, body)

        logging.info("🔗 Estableciendo canal cuántico con RabbitMQ...")
        logging.info("🛸 AGENT listo para recibir transmisiones. Esperando en la órbita...")
        consumer.consume(on_message)
    except Exception as e:
        logging.exception(f"💥 Error fatal en agent: {e}")
    finally:
        if consumer:
            try:
                consumer.close()
                logging.info("👋 Agent finalizado correctamente.")
            except Exception as e:
                logging.error(f"Error al cerrar consumer: {e}")

if __name__ == "__main__":
    load_dotenv()
    main()