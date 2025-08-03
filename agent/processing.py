import time
import random

class TaskProcessor:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def process_task(self, task_id):
        try:
            self.db_manager.update_task_status(task_id, 'IN_PROGRESS')
            self.db_manager.log_message(task_id, 'IN_PROGRESS', 'Task processing started.')

            # Simulate data scraping
            time.sleep(random.randint(1, 5))

            # Simulate random success or failure
            if random.random() < 0.1:
                raise ValueError("Random processing error")

            self.db_manager.update_task_status(task_id, 'DONE')
            self.db_manager.log_message(task_id, 'DONE', 'Task completed successfully.')

        except ValueError as e:
            error_message = f"ValueError: {e}"
            self.db_manager.update_task_status(task_id, 'ERROR_PROCESSING')
            self.db_manager.log_message(task_id, 'ERROR_PROCESSING', error_message)

        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            self.db_manager.update_task_status(task_id, 'ERROR_UNEXPECTED')
            self.db_manager.log_message(task_id, 'ERROR_UNEXPECTED', error_message)
