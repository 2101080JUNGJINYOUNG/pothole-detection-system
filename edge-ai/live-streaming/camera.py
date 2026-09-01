import cv2
import os
import requests
import time

from route_points import PRESET_POINTS  # map.py가 만든 좌표 리스트

# 🔹 서버 주소 (보낼 곳)
#   SERVER_URL: 서버로 프레임과 좌표를 전송하는 엔드포인트 URL
SERVER_URL = "http://localhost:8000/pothole"

# 🔹 테스트할 동영상 파일 이름
VIDEO_PATH = "test3.mp4"


def get_interpolated_coord(frame_idx: int, total_frames: int, points):
    """
    전체 프레임 수에 맞춰서
    PRESET_POINTS 사이를 선형 보간해서 (lat, lon)를 반환.
    - frame_idx: 1, 2, 3, ... (현재 프레임 번호)
    - total_frames: 전체 프레임 수
    - points: [(lat, lon), ...]
    """
    n = len(points)
    if n == 0:
        raise ValueError("PRESET_POINTS가 비어 있습니다.")
    if n == 1 or total_frames <= 1:
        # 포인트가 하나뿐이거나, 프레임 정보가 이상하면 그냥 첫 좌표 사용
        return points[0]

    # 0.0 ~ 1.0 사이 비율
    ratio = frame_idx / (total_frames - 1)

    # 0.0 ~ (n-1) 사이 실수 인덱스
    pos = ratio * (n - 1)

    i0 = int(pos)
    i1 = min(i0 + 1, n - 1)  # 마지막을 넘지 않도록
    alpha = pos - i0         # 0.0 ~ 1.0

    lat0, lon0 = points[i0]
    lat1, lon1 = points[i1]

    # 선형 보간 (linear interpolation)
    lat = lat0 + (lat1 - lat0) * alpha
    lon = lon0 + (lon1 - lon0) * alpha

    return lat, lon


def preview_and_send_video():
    # 1. 동영상 파일 체크
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ '{VIDEO_PATH}' 파일이 없습니다. 동영상 파일을 폴더에 넣어주세요!")
        return

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("❌ 동영상을 열 수 없습니다.")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    num_points = len(PRESET_POINTS)

    print(f"🎬 동영상: {VIDEO_PATH}")
    print(f"🎞  전체 프레임 수: {total_frames}")
    print(f"📍 PRESET_POINTS 개수: {num_points}")
    print(f"🌐 서버 URL: {SERVER_URL}")

    frame_count = 0

    # 🔹 HTTP 연결 재사용을 위해 세션 생성 (Session for faster HTTP requests)
    session = requests.Session()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("\n✅ 동영상 끝")
            break

        frame_count += 1

        # ✅ 보간된 좌표 구하기 (Get interpolated GPS coord for this frame)
        lat, lon = get_interpolated_coord(frame_count, total_frames, PRESET_POINTS)

        # 보기 편하게 리사이즈 (원하면 생략 가능)
        frame_resized = cv2.resize(frame, (640, 480))

        # ---- 서버로 전송용 이미지 인코딩 (JPEG 압축) ----
        # 라즈베리파이 환경처럼 JPG로 압축해서 보냄
        success, encoded_img = cv2.imencode(
            '.jpg',
            frame_resized,
            [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        )
        if not success:
            print(f"\n⚠️ 프레임 인코딩 실패 (frame {frame_count})")
            continue

        files = {
            'image': ('video_frame.jpg', encoded_img.tobytes(), 'image/jpeg')
        }
        data = {
            'latitude': f"{lat:.7f}",
            'longitude': f"{lon:.7f}",
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # ---- 서버로 전송 (Send frame + GPS to server) ----
        try:
            start_time = time.time()
            resp = session.post(SERVER_URL, files=files, data=data, timeout=2)
            elapsed_ms = (time.time() - start_time) * 1000

            if resp.status_code == 200:
                # 서버가 JSON으로 status를 돌려준다고 가정
                try:
                    res_json = resp.json()
                    status = res_json.get("status")
                except Exception:
                    status = None

                if status == "detected":
                    print(
                        f"\n[{frame_count}/{total_frames}] ✨ pothole detected!"
                        f" ({elapsed_ms:.1f} ms, lat={lat:.7f}, lon={lon:.7f})"
                    )
                else:
                    # 감지 안 된 프레임은 그냥 진행 중 표시
                    print(".", end="", flush=True)
                    if frame_count % 30 == 0:
                        print(
                            f" ({frame_count} frames, lat={lat:.5f}, lon={lon:.5f})"
                        )
            else:
                print(f"\n⚠️ 서버 응답 코드: {resp.status_code}")

        except Exception as e:
            print(f"\n❌ 서버 전송 중 오류 발생: {e}")
            # 필요하면 break() 해서 중단할 수도 있음
            # break

        # ---- 화면에 텍스트로 표시 (Preview on screen) ----
        text1 = f"Frame: {frame_count}/{total_frames}"
        text2 = f"Lat: {lat:.7f}, Lon: {lon:.7f}"

        cv2.putText(frame_resized, text1, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame_resized, text2, (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow("GPS + Server Stream", frame_resized)

        # ESC(27) 또는 q 눌러서 종료 (Press ESC or q to quit)
        key = cv2.waitKey(30) & 0xFF
        if key == 27 or key == ord('q'):
            print("\n🛑 사용자 종료")
            break

    cap.release()
    cv2.destroyAllWindows()
    print("👋 종료 완료")


if __name__ == "__main__":
    preview_and_send_video()
