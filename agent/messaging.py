import pika
import json
import time

class RabbitMQConsumer:
    def __init__(self, rabbitmq_uri, queue_name, task_processor):
        self.rabbitmq_uri = rabbitmq_uri
        self.queue_name = queue_name
        self.task_processor = task_processor
        self.connection = None
        self.channel = None

    def connect(self):
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_uri))
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                print("Connected to RabbitMQ.")
                break
            except pika.exceptions.AMQPConnectionError as e:
                print(f"Failed to connect to RabbitMQ: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    def _callback(self, ch, method, properties, body):
        try:
            task_data = json.loads(body)
            task_id = task_data.get('task_id')
            if task_id:
                print(f"Received task {task_id}")
                self.task_processor.process_task(task_id)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"Task {task_id} processed and acknowledged.")
            else:
                print("Received message without a task_id.")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except json.JSONDecodeError:
            print("Failed to decode message body.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            print(f"An error occurred in callback: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        if not self.channel or self.channel.is_closed:
            self.connect()

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self._callback)

        print('Waiting for messages. To exit press CTRL+C')
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop_consuming()
        except (pika.exceptions.ConnectionClosedByBroker, pika.exceptions.StreamLostError):
            print("Connection lost. Reconnecting...")
            # Simple reconnection logic
            self.start_consuming()

    def stop_consuming(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
        print("RabbitMQ connection closed.")
