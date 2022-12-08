# Added for group id (needed to force reset to load personStorage after every restart)
import time
import sys
sys.path.insert(0, '../')

import base64
import json
import os.path
import socket
import string
import random
import jsonpickle
import json

from confluent_kafka import Producer
from confluent_kafka import Consumer

from log import log_info, log_error

import face_rec

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
with open(BASE_PATH + '/../config.json') as json_config_file:
    config = json.load(json_config_file)

kafka_config = config['kafka']

in_topic = kafka_config['in_topic']
next_topic = kafka_config['next_topic']
out_topic = kafka_config['out_topic']
storage_topic = kafka_config['storage_topic']

kafka_ip = kafka_config['ip']
kafka_port = kafka_config['port']

# kafka_group_id_postfix = '-' + ''.join(random.choice(string.ascii_lowercase) for i in range(8))
kafka_group_id = "{}-{}".format(kafka_config['group_id'],time.time()) # kafka_config['group_id']  # + kafka_group_id_postfix

kafka_connection_string = kafka_ip + ':' + kafka_port

consumer = Consumer({
    'bootstrap.servers': kafka_connection_string,
    'group.id': "{}-{}".format(kafka_group_id,time.time()),
    'auto.offset.reset': 'earliest'
})

personStorage = {}

consumer.subscribe(["personStorage"])
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
        data = json.loads(decoded_message)
        #if not data["id"] in personStorage:
        log_info("Added {} to local person Storage".format(data["name"]))
        if data["id"] == "":
            continue

        data["vector"] = json.loads(data["vector"])

        personStorage[data["id"]] = {
            "id": data["id"],
            "name": data["name"],
            "vector": data["vector"]
        }

        #print(decoded_message)
        person_array = [k["vector"] for k in personStorage.values()]
        #print(personStorage)
        #print(personStorage.values())
except KeyboardInterrupt:
    log_info('Interrupt received - shutting down')
    pass

consumer.close()
log_info('Shutdown complete')