import cv2
import yaml
from confluent_kafka import Producer
import json

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
    producer_conf = {'bootstrap.servers': config['kafka']['bootstrap_servers']}
    producer = Producer(producer_conf)
    topic = config['kafka']['topic']
    
    cap = cv2.VideoCapture(config['video']['input_path'])
    frame_num = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Chuyển khung hình thành byte array
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        # Gửi khung hình qua Kafka
        message = {
            'frame_num': frame_num,
            'frame': frame_bytes.hex()  # Chuyển thành hex để gửi an toàn
        }
        producer.produce(topic, value=json.dumps(message).encode('utf-8'), callback=delivery_report)
        producer.poll(0)
        frame_num += 1
    
    # Gửi tín hiệu kết thúc
    end_message = {
        'frame_num': -1,
        'frame': 'EOF'
    }
    producer.produce(topic, value=json.dumps(end_message).encode('utf-8'), callback=delivery_report)

    producer.flush()
    cap.release()

if __name__ == "__main__":
    run_producer()