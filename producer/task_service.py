import json
import random
import time
from datetime import datetime

class TaskService:
    def __init__(self, db_manager, mq_producer):
        self.db_manager = db_manager
        self.mq_producer = mq_producer

    def run(self):
        print("Starting task generation...")
        self.mq_producer.connect()

        for i in range(10):
            task_data = self._generate_task_data(i)
            print(f"Generated task: {task_data}")

            try:
                task_id = self.db_manager.insert_task(json.dumps(task_data))
                print(f"Task {task_id} inserted into database.")
                self.db_manager.insert_log(task_id, "Task created and stored in DB.")

                task_body = json.dumps({'task_id': task_id, 'data': task_data})
                self.mq_producer.publish_task(task_body)
                print(f"Task {task_id} published to RabbitMQ.")
                self.db_manager.insert_log(task_id, "Task published to RabbitMQ.")

            except Exception as e:
                print(f"An error occurred processing task {i}: {e}")

            time.sleep(1)

        self.mq_producer.close()
        print("Finished generating tasks.")

    def _generate_task_data(self, index):
        return {
            "task_name": f"task_{index}",
            "timestamp": datetime.now().isoformat(),
            "random_number": random.randint(1, 1000)
        }
