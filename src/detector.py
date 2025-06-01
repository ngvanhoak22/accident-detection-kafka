from ultralytics import YOLO
import cv2

class Detector:
    def __init__(self, model_path, conf_threshold=0.5):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect_cars(self, frame):
        results = self.model(frame)
        detections = []
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            confidences = result.boxes.conf.cpu().numpy()
            classes = result.boxes.cls.cpu().numpy()
            for box, conf, cls in zip(boxes, confidences, classes):
                if self.model.names[int(cls)] == "car" and conf >= self.conf_threshold:
                    x1, y1, x2, y2 = box
                    detections.append({
                        "box": [x1, y1, x2, y2],
                        "confidence": conf,
                        "class": "car"
                    })
        return detections