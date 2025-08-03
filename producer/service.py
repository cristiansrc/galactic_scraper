from repository import TaskRepository
from messaging import RabbitMQProducer
import json

class TaskService:
    def __init__(self, repository: TaskRepository, producer: RabbitMQProducer):
        self.repository = repository
        self.producer = producer

    def create_and_publish_task(self, task):
        if not self.repository.task_exists(task["task_id"]):
            self.repository.insert_task(task)
            self.producer.publish(json.dumps(task))
            return True
        return False

    def process_tasks(self, tasks):
        for task in tasks:
            if not self.repository.task_exists(task["task_id"]):
                self.repository.insert_task(task)
                self.repository.insert_log(task["task_id"], "Tarea registrada en BD como PENDING")
        # Enviar a RabbitMQ y loguear
        for task in tasks:
            try:
                self.producer.publish(json.dumps(task))
                self.repository.insert_log(task["task_id"], "Tarea enviada a RabbitMQ", details=task)
            except Exception as e:
                self.repository.insert_log(task["task_id"], "Error al enviar a RabbitMQ", level="ERROR", details={"error": str(e)})
