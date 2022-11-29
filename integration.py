import base64
import json
import os.path

from confluent_kafka import Producer
from confluent_kafka import Consumer

import face_rec


class PersonData:
    def __init__(self, pId, croppedPicture, recognitionId, emotions):
        self.pId = pId
        self.croppedPicture = croppedPicture
        self.recognitionId = recognitionId
        self.emotions = emotions


class IdentificationRequest:
    def __init__(self, id, sourcePicture, persons):
        self.id = id
        self.sourcePicture = sourcePicture
        self.persons = persons


class IdentificationResult:
    def __init__(self, id, image, vector, recognitionId):
        self.id = id
        self.image = image
        self.vector = vector
        self.recognitionId = recognitionId


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

kafka_group_id = kafka_config['group_id']

kafka_connection_string = kafka_ip + ':' + kafka_port

consumer = Consumer({
    'bootstrap.servers': kafka_connection_string,
    'group.id': kafka_group_id,
    'auto.offset.reset': 'earliest'
})
producer = Producer({'bootstrap.servers': kafka_connection_string})

cache = {}


def handle_send_result(error, message):
    if error is not None:
        print('Message delivery failed')


def send(message, topic):
    producer.poll(0)
    producer.produce(topic, message, callback=handle_send_result)
    producer.flush()


def store(recognitionId, landmarks):
    message = {
        'id': recognitionId,
        'landmarks': landmarks
    }

    json_object = json.dumps(message)
    print('Trying to store: {}'.format(json_object))
    send(json_object, storage_topic)


def run():
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
        incoming_data = IdentificationRequest(data['id'], data['sourcePicture'], data['persons'])

        for person in incoming_data.persons:
            image_bytes = base64.b64decode(person['croppedPicture'])
            found, recognition_id, landmarks = face_rec.find_image_from_base64(person['croppedPicture'], cache)

            if recognition_id in cache:
                print("User already in cache - identified as {}".format(recognition_id))
                if not found:
                    print("User already in cache - no match")
            else:
                cache[person['recognitionId']] = landmarks
                print("User, {} added to cache".format(person['recognitionId']))

        send(decoded_message, next_topic)

    consumer.close()


run()
