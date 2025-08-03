from config import get_database_uri, get_rabbitmq_uri
from database import DatabaseManager
from messaging import RabbitMQProducer
from task_service import TaskService

def main():
    """Main function to run the producer."""
    db_uri = get_database_uri()
    rabbitmq_uri = get_rabbitmq_uri()

    if not db_uri or not rabbitmq_uri:
        print("Error: DATABASE_URL and RABBITMQ_URL must be set in .env file.")
        return

    db_manager = DatabaseManager(db_uri)
    mq_producer = RabbitMQProducer(rabbitmq_uri)
    task_service = TaskService(db_manager, mq_producer)

    task_service.run()

if __name__ == "__main__":
    main()
