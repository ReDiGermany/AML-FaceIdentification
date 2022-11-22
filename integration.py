import base64
import json
import os.path
import numpy as np

from confluent_kafka import Producer
from confluent_kafka import Consumer


class IdentificationRequest:
    def __init__(self, message_id, name, image):
        self.id = message_id
        self.name = name
        self.image = image


class IdentificationResult:
    def __init__(self, message_id, name, vector):
        self.id = message_id
        self.name = name
        self.vector = vector


BASE_PATH = os.path.dirname(os.path.realpath(__file__))
with open(BASE_PATH + '/config.json') as json_config_file:
    config = json.load(json_config_file)

kafka_config = config['kafka']

in_topic = kafka_config['in_topic']
out_topic = kafka_config['out_topic']

kafka_ip = kafka_config['ip']
kafka_port = kafka_config['port']

kafka_group_id = kafka_config['group_id']

kafka_connection_string = kafka_ip + ':' + kafka_port

consumer = Consumer({
    'bootstrap.servers': kafka_connection_string,
    'group.id': kafka_group_id,
    'auto.offset.reset': 'earliest'
})
producer = Producer({'bootstrap.servers': kafka_connection_string})


def test_callback(message):
    print('Received message: {}'.format(message))


def handle_send_result(error, message):
    if error is not None:
        print('Message delivery failed - trying to resend')
        send(message)


def send(message):
    producer.poll(0)
    producer.produce(out_topic, message, callback=handle_send_result)
    producer.flush()


def run(callback):
    consumer.subscribe([in_topic])
    print('Started')
    while True:
        message = consumer.poll(1.0)

        if message is None:
            continue
        if message.error():
            print('Consumer error: {}'.format(message.error()))
            continue

        decoded_message = message.value().decode('utf-8')

        data = json.loads(decoded_message)
        incoming_data = IdentificationRequest(data['message_id'], data['name'], data['image'])
        print(incoming_data.image)
        with open('imageToSave.jpeg', 'wb') as fh:
            fh.write(base64.b64decode(incoming_data.image))
        send(callback(decoded_message))

    consumer.close()


run(test_callback)
