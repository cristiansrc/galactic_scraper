import os
import signal
import sys
from config import get_database_uri, get_rabbitmq_uri
from database import DatabaseManager
from messaging import RabbitMQConsumer
from processing import TaskProcessor

def main():
    """
    Main function to initialize and run the agent.
    """
    db_uri = get_database_uri()
    rabbitmq_uri = get_rabbitmq_uri()
    queue_name = os.getenv("RABBITMQ_QUEUE", "task_queue")

    if not all([db_uri, rabbitmq_uri]):
        print("DATABASE_URL and RABBITMQ_URL must be set in the environment.", file=sys.stderr)
        sys.exit(1)

    db_manager = None
    consumer = None

    def shutdown_handler(signum, frame):
        print("\nShutdown signal received. Cleaning up...")
        if consumer:
            consumer.stop_consuming()
        if db_manager:
            db_manager.close()
        print("Cleanup complete. Exiting.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        db_manager = DatabaseManager(db_uri)
        task_processor = TaskProcessor(db_manager)
        consumer = RabbitMQConsumer(
            rabbitmq_uri=rabbitmq_uri,
            queue_name=queue_name,
            task_processor=task_processor
        )
        consumer.start_consuming()

    except Exception as e:
        print(f"An unhandled error occurred: {e}", file=sys.stderr)
        if consumer:
            consumer.stop_consuming()
        if db_manager:
            db_manager.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
