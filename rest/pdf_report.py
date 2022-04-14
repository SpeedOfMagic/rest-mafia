import pika
import uuid
from time import sleep


class QueueReader:
    QUEUE_NAME = 'pdf_queue'

    corr_id: str
    response: str or None

    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', heartbeat=0))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue='', exclusive=True, durable=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)
        self.response = None

    def on_response(self, _, __, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def generate_pdf(self, profile) -> str:
        self.corr_id = str(uuid.uuid4())
        self.response = None
        self.channel.basic_publish(
            exchange='',
            routing_key=self.QUEUE_NAME,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                delivery_mode=2,
                correlation_id=self.corr_id,
            ),
            body=str(vars(profile)))

        while self.response is None:
            self.connection.process_data_events()
            sleep(0.1)
        assert self.response is not None
        return self.response


reader = None


def generate_pdf_via_queue(profile):
    global reader
    if reader is None:
        reader = QueueReader()
    return reader.generate_pdf(profile)
