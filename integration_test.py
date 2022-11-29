import base64
import json
import os.path
import uuid

from confluent_kafka import Producer

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

producer = Producer({'bootstrap.servers': kafka_connection_string})

with open('images/charlene_von_monaco/charlene_von_monaco.jpeg', 'rb') as img:
    image = base64.b64encode(img.read())
message_uuid = uuid.uuid4().__str__()

message = {
    'id': message_uuid,
    'sourcePicture': image.decode('utf-8'),
    'persons': [
        {
            'pId': uuid.uuid4().__str__(),
            'croppedPicture': image.decode('utf-8'),
            'recognitionId': uuid.uuid4().__str__(),
            'emotions': []
        },
        {
            'pId': uuid.uuid4().__str__(),
            'croppedPicture': image.decode('utf-8'),
            'recognitionId': uuid.uuid4().__str__(),
            'emotions': []
        }

    ]
}

print(message_uuid)
print(image)

json_object = json.dumps(message)
producer.produce(in_topic, json_object)
producer.flush()
