import cv2
import yaml
import json
import time
from confluent_kafka import Consumer, KafkaError

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def run_consumer():
    config = load_config("configs/config.yaml")
    consumer_conf = {
        'bootstrap.servers': config['kafka']['bootstrap_servers'],
        'group.id': 'video-consumer-group',
        'auto.offset.reset': 'earliest',
        'socket.timeout.ms': 60000,
        'session.timeout.ms': 30000,
        'heartbeat.interval.ms': 10000,
        'debug': 'broker,topic,msg'
    }
    consumer = None
    retries = 20
    for i in range(retries):
        try:
            consumer = Consumer(consumer_conf)
            consumer.subscribe([config['kafka']['topic']])
            print("Connected to Kafka")
            break
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}. Retrying {i+1}/{retries}...")
            time.sleep(10)
    if consumer is None:
        raise Exception("Could not connect to Kafka after retries")

    out_path = config['video']['output_path']
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = None

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print("Reached end of partition")
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break

            data = json.loads(msg.value().decode('utf-8'))
            frame_num = data['frame_num']
            frame_bytes = bytes.fromhex(data['frame'])
            frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)

            if out is None:
                height, width = frame.shape[:2]
                out = cv2.VideoWriter(out_path, fourcc, 20.0, (width, height))

            out.write(frame)
            print(f"Processed frame {frame_num}")

    finally:
        if out is not None:
            out.release()
        consumer.close()

if __name__ == "__main__":
    import numpy as np
    run_consumer()