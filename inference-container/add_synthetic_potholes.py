"""
포트홀 합성 데이터를 기존 파인튜닝 데이터셋에 추가하는 스크립트
"""

import os
import sys
import argparse
from synthetic_pothole_generator import SyntheticPotholeGenerator


def add_synthetic_to_finetune_dataset(road_images_dir: str, 
                                     finetune_dataset_dir: str,
                                     num_potholes_per_image: int = 1):
    """
    합성 포트홀 데이터를 파인튜닝 데이터셋에 추가
    
    Args:
        road_images_dir: 포트홀이 없는 도로 이미지 디렉토리
        finetune_dataset_dir: 파인튜닝 데이터셋 디렉토리
        num_potholes_per_image: 이미지당 포트홀 개수
    """
    # 데이터셋 디렉토리 구조
    train_images_dir = os.path.join(finetune_dataset_dir, "images", "train")
    train_labels_dir = os.path.join(finetune_dataset_dir, "labels", "train")
    
    os.makedirs(train_images_dir, exist_ok=True)
    os.makedirs(train_labels_dir, exist_ok=True)
    
    # 기존 파일 개수 확인
    existing_images = len([f for f in os.listdir(train_images_dir) if f.endswith(('.jpg', '.jpeg', '.png'))])
    start_index = existing_images
    
    print(f"[INFO] 기존 이미지: {existing_images}개")
    print(f"[INFO] 합성 데이터 추가 시작 (시작 인덱스: {start_index})")
    
    # 생성기 초기화
    generator = SyntheticPotholeGenerator()
    
    # 합성 데이터 생성
    stats = generator.generate_synthetic_dataset(
        road_images_dir=road_images_dir,
        output_images_dir=train_images_dir,
        output_labels_dir=train_labels_dir,
        num_potholes_per_image=num_potholes_per_image,
        min_scale=0.4,
        max_scale=2.0,
        class_id=0
    )
    
    print(f"[OK] 합성 데이터 추가 완료:")
    print(f"  - 처리된 이미지: {stats['processed_images']}개")
    print(f"  - 생성된 포트홀: {stats['total_potholes']}개")
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="파인튜닝 데이터셋에 합성 포트홀 데이터 추가")
    parser.add_argument('--road_images', type=str, required=True,
                       help='포트홀이 없는 도로 이미지 디렉토리')
    parser.add_argument('--dataset_dir', type=str, required=True,
                       help='파인튜닝 데이터셋 디렉토리')
    parser.add_argument('--num_potholes', type=int, default=1,
                       help='이미지당 포트홀 개수 (기본값: 1)')
    
    args = parser.parse_args()
    
    add_synthetic_to_finetune_dataset(
        road_images_dir=args.road_images,
        finetune_dataset_dir=args.dataset_dir,
        num_potholes_per_image=args.num_potholes
    )


if __name__ == "__main__":
    main()


