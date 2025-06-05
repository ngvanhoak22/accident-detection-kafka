import numpy as np

def calculate_iou(box1, box2):
    x1, y1, x2, y2 = box1
    x1_, y1_, x2_, y2_ = box2
    xi1, yi1 = max(x1, x1_), max(y1, y1_)
    xi2, yi2 = min(x2, x2_), min(y2, y2_)
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1) 
    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (x2_ - x1_) * (y2_ - y1_)
    union_area = box1_area + box2_area - inter_area
    return inter_area / union_area if union_area > 0 else 0

def detect_collisions(tracked_objects, min_iou=0.1):
    collisions = []
    for i, (id1, box1) in enumerate(tracked_objects):
        for j, (id2, box2) in enumerate(tracked_objects[i+1:], i+1):
            iou = calculate_iou(box1, box2)
            if iou > min_iou:
                collisions.append((id1, id2, iou))
    return collisions