"""
전체 파이프라인 테스트 스크립트
이미지 또는 영상 파일로 전체 파이프라인을 테스트합니다.
"""

import sys
import os

# AI Core 모듈 경로 추가
sys.path.insert(0, '/app')

from main import AICore

def test_image_pipeline(image_path, latitude=None, longitude=None):
    """
    이미지 파일로 파이프라인 테스트
    
    Args:
        image_path: 테스트할 이미지 파일 경로
        latitude: GPS 위도 (선택사항)
        longitude: GPS 경도 (선택사항)
    """
    print("=" * 60)
    print("전체 파이프라인 테스트 시작")
    print("=" * 60)
    
    # AI Core 초기화
    print("\n[1/5] AI Core 초기화 중...")
    ai_core = AICore()
    print("[OK] AI Core 초기화 완료")
    
    # 이미지 파일 확인
    print(f"\n[2/5] 이미지 파일 확인: {image_path}")
    if not os.path.exists(image_path):
        print(f"[ERROR] 이미지 파일을 찾을 수 없습니다: {image_path}")
        return False
    print("[OK] 이미지 파일 확인 완료")
    
    # GPS 좌표 확인
    if latitude is None or longitude is None:
        print("\n[3/5] GPS 좌표 추출 시도...")
        lat, lon = ai_core.get_gps_from_image(image_path)
        if lat is not None and lon is not None:
            latitude = lat
            longitude = lon
            print(f"[OK] GPS 좌표 추출 성공: {latitude:.6f}, {longitude:.6f}")
        else:
            latitude = latitude if latitude is not None else 37.5665
            longitude = longitude if longitude is not None else 126.9780
            print(f"[INFO] GPS 좌표 없음, 기본값 사용: {latitude}, {longitude}")
    else:
        print(f"\n[3/5] GPS 좌표 사용: {latitude}, {longitude}")
    
    # 이미지 처리
    print("\n[4/5] 이미지 처리 시작...")
    print("-" * 60)
    ai_core.process_image(image_path, latitude, longitude)
    print("-" * 60)
    print("[OK] 이미지 처리 완료")
    
    # 결과 확인
    print("\n[5/5] 데이터베이스 저장 확인...")
    try:
        cursor = ai_core.db_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count, 
                   MAX(detected_at) as last_detection
            FROM potholes
            WHERE image_path = %s
        """, (image_path,))
        result = cursor.fetchone()
        cursor.close()
        
        if result and result[0] > 0:
            print(f"[OK] 데이터베이스에 {result[0]}개의 레코드 저장됨")
            print(f"[OK] 최근 탐지 시간: {result[1]}")
            return True
        else:
            print("[WARNING] 데이터베이스에 저장된 레코드가 없습니다.")
            print("         (포트홀이 탐지되지 않았거나 검증에 실패했을 수 있습니다)")
            return False
    except Exception as e:
        print(f"[ERROR] 데이터베이스 확인 실패: {str(e)}")
        return False

def test_video_pipeline(video_path, latitude=None, longitude=None):
    """
    영상 파일로 파이프라인 테스트
    
    Args:
        video_path: 테스트할 영상 파일 경로
        latitude: GPS 위도 (선택사항)
        longitude: GPS 경도 (선택사항)
    """
    print("=" * 60)
    print("전체 파이프라인 테스트 시작 (영상)")
    print("=" * 60)
    
    # AI Core 초기화
    print("\n[1/4] AI Core 초기화 중...")
    ai_core = AICore()
    print("[OK] AI Core 초기화 완료")
    
    # 영상 파일 확인
    print(f"\n[2/4] 영상 파일 확인: {video_path}")
    if not os.path.exists(video_path):
        print(f"[ERROR] 영상 파일을 찾을 수 없습니다: {video_path}")
        return False
    print("[OK] 영상 파일 확인 완료")
    
    # 영상 처리
    print("\n[3/4] 영상 처리 시작...")
    print("-" * 60)
    ai_core.process_video(video_path, latitude, longitude, frame_interval=30)
    print("-" * 60)
    print("[OK] 영상 처리 완료")
    
    # 결과 확인
    print("\n[4/4] 데이터베이스 저장 확인...")
    try:
        cursor = ai_core.db_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count, 
                   MAX(detected_at) as last_detection
            FROM potholes
            WHERE detected_at >= NOW() - INTERVAL '5 minutes'
        """)
        result = cursor.fetchone()
        cursor.close()
        
        if result and result[0] > 0:
            print(f"[OK] 최근 5분간 {result[0]}개의 레코드 저장됨")
            print(f"[OK] 최근 탐지 시간: {result[1]}")
            return True
        else:
            print("[WARNING] 최근 5분간 데이터베이스에 저장된 레코드가 없습니다.")
            return False
    except Exception as e:
        print(f"[ERROR] 데이터베이스 확인 실패: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="전체 파이프라인 테스트")
    parser.add_argument("--image", type=str, help="테스트할 이미지 파일 경로")
    parser.add_argument("--video", type=str, help="테스트할 영상 파일 경로")
    parser.add_argument("--lat", type=float, help="GPS 위도")
    parser.add_argument("--lon", type=float, help="GPS 경도")
    
    args = parser.parse_args()
    
    if args.image:
        success = test_image_pipeline(args.image, args.lat, args.lon)
        sys.exit(0 if success else 1)
    elif args.video:
        success = test_video_pipeline(args.video, args.lat, args.lon)
        sys.exit(0 if success else 1)
    else:
        print("사용법:")
        print("  이미지 테스트: python test_pipeline.py --image <이미지경로> [--lat <위도>] [--lon <경도>]")
        print("  영상 테스트: python test_pipeline.py --video <영상경로> [--lat <위도>] [--lon <경도>]")
        sys.exit(1)



