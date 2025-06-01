import numpy as np

class Tracker:
    def __init__(self, max_distance=100):
        self.trackers = []  # Lưu danh sách ô tô: {"id": id, "box": [x1, y1, x2, y2]}
        self.next_id = 0
        self.max_distance = max_distance

    def update(self, detections):
        # Tính trung tâm hộp giới hạn cho các detection mới
        new_centers = [((det["box"][0] + det["box"][2]) / 2, (det["box"][1] + det["box"][3]) / 2)
                       for det in detections]

        # Tính trung tâm cho các tracker hiện có
        old_centers = [((t["box"][0] + t["box"][2]) / 2, (t["box"][1] + t["box"][3]) / 2)
                       for t in self.trackers]

        # Tính ma trận khoảng cách
        cost_matrix = np.zeros((len(old_centers), len(new_centers)))
        for i, old_c in enumerate(old_centers):
            for j, new_c in enumerate(new_centers):
                cost_matrix[i, j] = np.sqrt((old_c[0] - new_c[0])**2 + (old_c[1] - new_c[1])**2)

        # Gán ID dựa trên khoảng cách
        updated_trackers = []
        matched_dets = set()
        if old_centers and new_centers:
            from scipy.optimize import linear_sum_assignment
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
            for i, j in zip(row_ind, col_ind):
                if cost_matrix[i, j] < self.max_distance:
                    self.trackers[i]["box"] = detections[j]["box"]
                    updated_trackers.append(self.trackers[i])
                    matched_dets.add(j)

        # Thêm các detection mới chưa được khớp
        for j, det in enumerate(detections):
            if j not in matched_dets:
                updated_trackers.append({"id": self.next_id, "box": det["box"]})
                self.next_id += 1

        self.trackers = updated_trackers
        return [(t["id"], t["box"]) for t in self.trackers]