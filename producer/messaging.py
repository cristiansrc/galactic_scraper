import pika

class RabbitMQProducer:
    def __init__(self, rabbit_params):
        self.rabbit_params = rabbit_params
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=self.rabbit_params["host"],
            credentials=pika.PlainCredentials(
                self.rabbit_params["user"],
                self.rabbit_params["password"]
            )
        ))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.rabbit_params["queue"], durable=True)

    def publish(self, message):
        self.channel.basic_publish(
            exchange='',
            routing_key=self.rabbit_params["queue"],
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def close(self):
        self.connection.close()
