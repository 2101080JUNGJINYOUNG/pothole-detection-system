"""
포트홀 합성 데이터셋 생성 스크립트
도로 이미지에 AI로 생성된 포트홀을 합성하여 학습 데이터 생성
"""

import os
import sys
import argparse
from synthetic_pothole_generator import SyntheticPotholeGenerator


def main():
    parser = argparse.ArgumentParser(
        description="생성형 AI를 사용하여 포트홀 합성 데이터셋 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 사용 (이미지당 포트홀 1개)
  python generate_synthetic_potholes.py \\
    --road_images /app/shared_images/detections \\
    --output_dir /app/models/synthetic_dataset
  
  # 이미지당 포트홀 2개, 다양한 크기
  python generate_synthetic_potholes.py \\
    --road_images /app/shared_images/detections \\
    --output_dir /app/models/synthetic_dataset \\
    --num_potholes 2 \\
    --min_scale 0.3 \\
    --max_scale 2.0
        """
    )
    
    parser.add_argument('--road_images', type=str, required=True,
                       help='도로 이미지가 있는 디렉토리 경로')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='출력 디렉토리 (이미지와 라벨이 저장됨)')
    parser.add_argument('--num_potholes', type=int, default=1,
                       help='이미지당 포트홀 개수 (기본값: 1)')
    parser.add_argument('--min_scale', type=float, default=0.5,
                       help='최소 포트홀 크기 스케일 (기본값: 0.5)')
    parser.add_argument('--max_scale', type=float, default=1.5,
                       help='최대 포트홀 크기 스케일 (기본값: 1.5)')
    parser.add_argument('--class_id', type=int, default=0,
                       help='YOLO 클래스 ID (기본값: 0)')
    
    args = parser.parse_args()
    
    # 디렉토리 확인
    if not os.path.exists(args.road_images):
        print(f"오류: 도로 이미지 디렉토리를 찾을 수 없습니다: {args.road_images}")
        sys.exit(1)
    
    # 출력 디렉토리 설정
    output_images_dir = os.path.join(args.output_dir, "images", "train")
    output_labels_dir = os.path.join(args.output_dir, "labels", "train")
    
    print("=" * 60)
    print("포트홀 합성 데이터셋 생성기")
    print("=" * 60)
    print(f"도로 이미지 디렉토리: {args.road_images}")
    print(f"출력 디렉토리: {args.output_dir}")
    print(f"이미지당 포트홀 개수: {args.num_potholes}")
    print(f"포트홀 크기 범위: {args.min_scale} ~ {args.max_scale}")
    print("=" * 60)
    print()
    
    # 생성기 초기화
    generator = SyntheticPotholeGenerator()
    
    # 데이터셋 생성
    print("합성 데이터셋 생성 시작...")
    stats = generator.generate_synthetic_dataset(
        road_images_dir=args.road_images,
        output_images_dir=output_images_dir,
        output_labels_dir=output_labels_dir,
        num_potholes_per_image=args.num_potholes,
        min_scale=args.min_scale,
        max_scale=args.max_scale,
        class_id=args.class_id
    )
    
    # 결과 출력
    print()
    print("=" * 60)
    print("생성 완료!")
    print("=" * 60)
    print(f"총 이미지: {stats['total_images']}")
    print(f"처리된 이미지: {stats['processed_images']}")
    print(f"생성된 포트홀: {stats['total_potholes']}")
    print(f"실패: {stats['failed']}")
    print("=" * 60)
    print(f"\n출력 위치:")
    print(f"  - 이미지: {output_images_dir}")
    print(f"  - 라벨: {output_labels_dir}")
    print()
    print("이제 이 데이터셋을 YOLO 학습에 사용할 수 있습니다!")


if __name__ == "__main__":
    main()


