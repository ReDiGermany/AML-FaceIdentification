import base64
import json
import os.path
import socket
import string
import random
import jsonpickle

from confluent_kafka import Producer
from confluent_kafka import Consumer

from log import log_info, log_error

import face_rec


class PersonData:
    def __init__(self, p_id, cropped_picture):
        self.pId = p_id
        self.croppedPicture = cropped_picture
        self.recognitionId = ''
        self.emotions = ''
        self.name = ''
        self.vector = ''


class IdentificationRequest:
    def __init__(self, message_id, source_picture, persons):
        self.id = message_id
        self.sourcePicture = source_picture
        self.persons = persons


class IdentificationResult:
    def __init__(self, message_id, source_picture, persons):
        self.id = message_id
        self.sourcePicture = source_picture
        self.persons = persons


BASE_PATH = os.path.dirname(os.path.realpath(__file__))
with open(BASE_PATH + '/config.json') as json_config_file:
    config = json.load(json_config_file)

kafka_config = config['kafka']

in_topic = kafka_config['in_topic']
next_topic = kafka_config['next_topic']
out_topic = kafka_config['out_topic']
storage_topic = kafka_config['storage_topic']

kafka_ip = kafka_config['ip']
kafka_port = kafka_config['port']

# kafka_group_id_postfix = '-' + ''.join(random.choice(string.ascii_lowercase) for i in range(8))
kafka_group_id = kafka_config['group_id']  # + kafka_group_id_postfix

kafka_connection_string = kafka_ip + ':' + kafka_port

consumer = Consumer({
    'bootstrap.servers': kafka_connection_string,
    'group.id': kafka_group_id,
    'auto.offset.reset': 'earliest'
})
producer = Producer({
    'bootstrap.servers': kafka_connection_string,
    'client.id': socket.gethostname()
})

cache = {}


def face_not_found_response():
    log_info('No face found')


def handle_send_result(error, message):
    if error is not None:
        log_error('Message delivery failed')
    else:
        log_info('Message delivered')


def send(message, topic):
    producer.poll(0)
    producer.produce(topic, message, callback=handle_send_result)
    producer.flush()


def store(recognition_id, landmarks):
    message = {
        'id': recognition_id,
        'landmarks': landmarks
    }

    json_object = json.dumps(message)
    log_info('Trying to store: {}'.format(json_object))


def run():
    consumer.subscribe([in_topic])
    log_info('Started')
    try:
        while True:
            message = consumer.poll(1.0)

            if message is None:
                log_info('no data in incoming topic')
                continue
            if message.error():
                log_error('Consumer error: {}'.format(message.error()))
                continue

            decoded_message = message.value().decode('utf-8')

            data = jsonpickle.decode(decoded_message)

            try:
                incoming_data = IdentificationRequest(data['id'], data['sourcePicture'], data['persons'])
            except KeyError:
                log_error('Message format incorrect - skipping message')
                continue

            person_response = []

            for person in incoming_data.persons:
                try:
                    p = PersonData(
                        person['pId'],
                        person['croppedPicture']
                        # person['recognitionId'],
                        # person['emotions'],
                        # person['name'],
                        # person['vector']
                    )
                except KeyError:
                    log_error('Message format incorrect - skipping message')
                    continue

                # image_bytes = base64.b64decode(person['croppedPicture'])
                found, recognition_id, landmarks = face_rec.find_image_from_base64(person['croppedPicture'], cache)

                if recognition_id in cache:
                    log_info('Person already in cache - identified as {}'.format(recognition_id))
                    p.recognitionId = recognition_id
                else:
                    if landmarks:
                        cache[person['pId']] = landmarks
                        log_info('Person, {} added to cache'.format(person['pId']))
                    else:
                        face_not_found_response()
                        continue

                p.vector = landmarks

                person_response.append(p)

            response = IdentificationResult(
                incoming_data.id,
                incoming_data.sourcePicture,
                person_response,
            )

            # print(jsonpickle.encode(response, unpicklable=False))

            send(jsonpickle.encode(response, unpicklable=False), next_topic)
    except KeyboardInterrupt:
        log_info('Interrupt received - shutting down')
        pass

    consumer.close()
    log_info('Shutdown complete')


run()
