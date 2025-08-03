import pika

class RabbitMQProducer:
    def __init__(self, amqp_uri):
        self.amqp_uri = amqp_uri
        self.connection = None
        self.channel = None

    def connect(self):
        self.connection = pika.BlockingConnection(pika.URLParameters(self.amqp_uri))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='task_queue', durable=True)

    def publish_task(self, task_body):
        if not self.channel or self.channel.is_closed:
            self.connect()
        
        self.channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=task_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
