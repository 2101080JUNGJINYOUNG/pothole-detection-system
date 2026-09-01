# local_worker.py
import socket
import struct
import cv2
import numpy as np
import torch
from ultralytics import YOLO
import sqlite3
import threading
import time
import base64
import requests
from queue import Queue

# -------------------------------
# 설정
# -------------------------------
UDP_IP = "0.0.0.0"
UDP_PORT = 8000
SERVER_URL = "http://127.0.0.1:8001/upload_blob"
DB_FILE = "pothole_local.db"

# GPU 설정
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔥 추론 장치: {device}")

# YOLO 모델 로드
model = YOLO("dec2.pt")
model.to(device)

# Local SQLite DB
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS potholes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image BLOB NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    uploaded INTEGER DEFAULT 0,
    timestamp TEXT DEFAULT (datetime('now', 'localtime'))
)
''')
conn.commit()

# -------------------------------
# IoU + 쿨다운 설정
# -------------------------------
IOU_THRESHOLD = 0.5
COOLDOWN = 0.5  # 초
previous_boxes = []
last_saved_time = 0

# 업로드 큐
upload_queue = Queue()

# -------------------------------
# IoU 계산 함수
# -------------------------------
def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    denom = float(boxAArea + boxBArea - interArea)
    return interArea / denom if denom != 0 else 0

# -------------------------------
# UDP 수신 + YOLO 감지 + 화면 송출
# -------------------------------
def udp_receive():
    global previous_boxes, last_saved_time
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"📡 UDP 서버 시작 (Port: {UDP_PORT})")

    prev_time = time.time()

    while True:
        try:
            data, addr = sock.recvfrom(65535)
            if len(data) <= 8:
                continue

            lat, lon = struct.unpack("ff", data[:8])
            image_data = data[8:]
            nparr = np.frombuffer(image_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # YOLO 추론 (로그 제거)
            results = model(frame, conf=0.5, device=0 if device=="cuda" else -1, verbose=False)
            boxes = results[0].boxes.xyxy.cpu().numpy() if results[0].boxes is not None else []
            detected = len(boxes) > 0

            # 화면용: 바운딩박스 표시
            annotated_frame = results[0].plot() if detected else frame.copy()
            annotated_frame1 = results[0].plot() if detected else frame.copy()

            # FPS 계산
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0.0
            prev_time = curr_time

            status_text = "DETECTED!" if detected else "Normal"
            color = (0,0,255) if detected else (0,255,0)
            cv2.putText(annotated_frame, status_text, (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (10,80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
            cv2.putText(annotated_frame, f"GPS: {lat:.5f}, {lon:.5f}", (10,120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

            # 화면 송출
            cv2.imshow("YOLO Monitor", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # DB 저장용: IoU + 쿨다운
            for box in boxes:
                is_new = True
                for prev_box in previous_boxes:
                    if iou(box, prev_box) > IOU_THRESHOLD:
                        is_new = False
                        break

                if is_new and (time.time() - last_saved_time) > COOLDOWN:
                    _, img_encoded = cv2.imencode(".jpg", annotated_frame1)
                    cur.execute(
                        "INSERT INTO potholes (image, latitude, longitude) VALUES (?, ?, ?)",
                        (img_encoded.tobytes(), lat, lon)
                    )
                    pothole_id = cur.lastrowid
                    conn.commit()
                    last_saved_time = time.time()
                    upload_queue.put(pothole_id)
                    previous_boxes.append(box)
                    print(f"✨ 로컬 DB 저장 → ID {pothole_id}, lat={lat:.5f}, lon={lon:.5f}")

            if len(previous_boxes) > 100:
                previous_boxes = previous_boxes[-50:]

        except Exception as e:
            print(f"UDP 에러: {e}")

    cv2.destroyAllWindows()

# -------------------------------
# 서버 업로드 워커
# -------------------------------
def upload_worker():
    while True:
        try:
            pothole_id = upload_queue.get()
            cur.execute("SELECT id, image, latitude, longitude FROM potholes WHERE id=?", (pothole_id,))
            row = cur.fetchone()
            if row:
                img_b64 = base64.b64encode(row[1]).decode("utf-8")
                payload = {"image_b64": img_b64, "latitude": row[2], "longitude": row[3]}
                try:
                    resp = requests.post(SERVER_URL, json=payload, timeout=5)
                    if resp.status_code == 200:
                        cur.execute("UPDATE potholes SET uploaded=1 WHERE id=?", (pothole_id,))
                        conn.commit()
                        print(f"🚀 서버 업로드 완료 → ID {pothole_id}")
                    else:
                        print(f"[UPLOAD] 실패 → ID {pothole_id}, status={resp.status_code}")
                except Exception as e:
                    print(f"[UPLOAD] 예외 발생 → ID {pothole_id}, error={e}")
        except Exception as e:
            print(f"[UPLOAD WORKER] 예외: {e}")
        time.sleep(0.01)  # 아주 짧은 sleep으로 CPU 점유 낮춤

# -------------------------------
# 스레드 시작
# -------------------------------
if __name__ == "__main__":
    t1 = threading.Thread(target=udp_receive)
    t1.daemon = True
    t1.start()

    t2 = threading.Thread(target=upload_worker)
    t2.daemon = True
    t2.start()

    print("📡 로컬 DB + 서버 업로드 워커 시작됨")

    while True:
        time.sleep(1)
