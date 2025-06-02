import cv2
import time
import yaml
import numpy as np
import json
from confluent_kafka import Consumer
from detector import Detector
from tracker import Tracker
from collision_detector import detect_collisions

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def log_collision(log_path, frame_num, id1, id2, iou):
    with open(log_path, 'a', encoding='utf-8') as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] Frame {frame_num}: Collision between Car {id1} and Car {id2} (IoU: {iou:.2f})\n")

def run_consumer():
    config = load_config("configs/config.yaml")
    consumer_conf = {
        'bootstrap.servers': config['kafka']['bootstrap_servers'],
        'group.id': 'video_processor',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe([config['kafka']['topic']])
    
    detector = Detector(config["model"]["path"], config["model"]["confidence_threshold"])
    tracker = Tracker(config["tracker"]["max_distance"])
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(config["video"]["output_path"], fourcc, 30.0, (1280, 720))  # Giả sử độ phân giải 1280x720

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        
        # Giải mã khung hình
        message = json.loads(msg.value().decode('utf-8'))
        #  Kiểm tra tín hiệu kết thúc
        if message.get("frame_num") == -1 and message.get("frame") == "EOF":
            print("Đã nhận EOF - thoát chương trình.")
            break
        frame_num = message['frame_num']
        frame_bytes = bytes.fromhex(message['frame'])
        frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        # Phát hiện ô tô
        detections = detector.detect_cars(frame)
        
        # Theo dõi và gán ID
        tracked_objects = tracker.update(detections)
        
        # Phát hiện va chạm
        collisions = detect_collisions(tracked_objects, config["collision"]["min_iou"])
        
        # Vẽ hộp giới hạn và ID
        for id_, box in tracked_objects:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, f"ID {id_}", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        
        # Vẽ và ghi log va chạm
        for id1, id2, iou in collisions:
            cv2.putText(frame, f"Collision: ID {id1} & ID {id2} (IoU: {iou:.2f})",
                        (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            log_collision(config["log"]["path"], frame_num, id1, id2, iou)
        
        out.write(frame)
        cv2.imshow("System", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    consumer.close()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_consumer()