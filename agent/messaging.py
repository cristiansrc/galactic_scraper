import pika

class RabbitMQConsumer:
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

    def consume(self, callback):
        self.channel.basic_consume(queue=self.rabbit_params["queue"], on_message_callback=callback)
        self.channel.start_consuming()

    def ack(self, delivery_tag):
        self.channel.basic_ack(delivery_tag=delivery_tag)

    def close(self):
        self.connection.close()

