import cv2
import yaml
from confluent_kafka import Producer, KafkaError
import json
import time

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def run_producer():
    config = load_config("configs/config.yaml")
    producer_conf = {
        'bootstrap.servers': config['kafka']['bootstrap_servers'],
        'error_cb': lambda err: print(f"Kafka error: {err}"),
        'client.id': 'video-producer',
        'socket.timeout.ms': 60000,
        'message.timeout.ms': 60000,
        'connections.max.idle.ms': 300000,
        'retry.backoff.ms': 500,
        'max.in.flight.requests.per.connection': 1,
        'debug': 'broker,topic,msg',
        'metadata.max.age.ms': 300000,
        'linger.ms': 10,  # Tăng thời gian chờ trước khi gửi
        'queue.buffering.max.messages': 100000,  # Tăng hàng đợi
    }
    producer = None
    retries = 20
    for i in range(retries):
        try:
            producer = Producer(producer_conf)
            # Chờ xử lý các sự kiện kết nối
            for _ in range(30):  # Thử 30 lần poll (tương đương 30 giây)
                producer.poll(1.0)  # Poll mỗi giây
                if producer is not None:
                    print(f"Connected to Kafka at {config['kafka']['bootstrap_servers']}")
                    break
            if producer is None:
                raise Exception("Failed to initialize producer")
            break
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}. Retrying {i+1}/{retries}...")
            time.sleep(10)
    if producer is None:
        raise Exception("Could not connect to Kafka after retries")

    topic = config['kafka']['topic']
    
    cap = cv2.VideoCapture(config['video']['input_path'])
    if not cap.isOpened():
        raise Exception("Could not open video file")
    
    frame_num = 0
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            message = {
                'frame_num': frame_num,
                'frame': frame_bytes.hex()
            }
            try:
                producer.produce(topic, value=json.dumps(message).encode('utf-8'), callback=delivery_report)
                producer.poll(1.0)  # Poll để xử lý callback
                print(f"Sent frame {frame_num}")
            except Exception as e:
                print(f"Failed to produce message: {e}")
            
            frame_num += 1
    finally:
        print("Flushing remaining messages...")
        producer.flush()
        cap.release()
        print("Producer finished.")

if __name__ == "__main__":
    run_producer()