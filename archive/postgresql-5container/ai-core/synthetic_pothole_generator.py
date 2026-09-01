"""
생성형 AI를 사용한 포트홀 합성 도구
도로 이미지에 AI로 생성된 포트홀을 자연스럽게 합성하여 학습 데이터 생성
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import requests
import json
import random
from typing import Tuple, List, Optional, Dict
import shutil

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: Google Generative AI가 설치되지 않았습니다.")


class SyntheticPotholeGenerator:
    """생성형 AI를 사용하여 포트홀을 합성하는 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API 키 (None이면 환경 변수에서 가져옴)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if GEMINI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.gemini_available = True
        else:
            self.gemini_available = False
            print("Warning: Gemini API를 사용할 수 없습니다.")
    
    def generate_pothole_image_with_gemini(self, road_type: str = "asphalt", size: Tuple[int, int] = (200, 200)) -> Optional[np.ndarray]:
        """
        Gemini를 사용하여 포트홀 이미지 생성
        
        Args:
            road_type: 도로 유형 ("asphalt", "concrete", "gravel")
            size: 생성할 이미지 크기 (width, height)
            
        Returns:
            포트홀 이미지 (numpy array, BGR 형식) 또는 None
        """
        if not self.gemini_available:
            return None
        
        try:
            # Gemini 2.0 Flash는 이미지 생성이 제한적이므로,
            # 대신 간단한 포트홀 텍스처를 생성하는 방법 사용
            # 실제로는 다른 생성형 AI(DALL-E, Stable Diffusion)를 사용하는 것이 더 좋습니다
            
            # 여기서는 프로그래밍 방식으로 포트홀 텍스처를 생성
            return self._generate_pothole_texture(size, road_type)
            
        except Exception as e:
            print(f"포트홀 이미지 생성 실패: {str(e)}")
            return None
    
    def _generate_pothole_texture(self, size: Tuple[int, int], road_type: str) -> np.ndarray:
        """
        프로그래밍 방식으로 포트홀 텍스처 생성
        (실제 생성형 AI 대신 사용)
        
        Args:
            size: 이미지 크기
            road_type: 도로 유형
            
        Returns:
            포트홀 텍스처 이미지 (numpy array, BGR)
        """
        width, height = size
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 도로 기본 색상
        if road_type == "asphalt":
            base_color = (80, 80, 80)  # 어두운 회색
        elif road_type == "concrete":
            base_color = (180, 180, 180)  # 밝은 회색
        else:  # gravel
            base_color = (120, 100, 80)  # 갈색
        
        img[:, :] = base_color
        
        # 랜덤 노이즈 추가 (도로 텍스처)
        noise = np.random.randint(-20, 20, (height, width, 3), dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # 포트홀 모양 생성 (타원형)
        center_x, center_y = width // 2, height // 2
        ellipse_w = random.randint(width // 3, width // 2)
        ellipse_h = random.randint(height // 3, height // 2)
        
        # 포트홀 안쪽 (어두운 색)
        cv2.ellipse(img, (center_x, center_y), (ellipse_w, ellipse_h), 
                    random.randint(0, 360), 0, 360, (40, 40, 40), -1)
        
        # 포트홀 가장자리 (그라데이션)
        for i in range(1, 10):
            alpha = i / 10.0
            color = tuple(int(base_color[j] * alpha + 40 * (1 - alpha)) for j in range(3))
            cv2.ellipse(img, (center_x, center_y), 
                       (int(ellipse_w * (1 - i * 0.05)), int(ellipse_h * (1 - i * 0.05))), 
                       random.randint(0, 360), 0, 360, color, 2)
        
        # 포트홀 내부 디테일 (균열, 그림자)
        for _ in range(random.randint(2, 5)):
            x = random.randint(center_x - ellipse_w // 2, center_x + ellipse_w // 2)
            y = random.randint(center_y - ellipse_h // 2, center_y + ellipse_h // 2)
            if ((x - center_x) ** 2 / (ellipse_w // 2) ** 2 + 
                (y - center_y) ** 2 / (ellipse_h // 2) ** 2) < 1:
                cv2.circle(img, (x, y), random.randint(2, 5), (20, 20, 20), -1)
        
        return img
    
    def composite_pothole_on_road(self, 
                                  road_image: np.ndarray, 
                                  pothole_image: np.ndarray,
                                  position: Optional[Tuple[int, int]] = None,
                                  scale: float = 1.0,
                                  rotation: float = 0.0,
                                  blend_mode: str = "normal") -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        포트홀 이미지를 도로 이미지에 자연스럽게 합성
        
        Args:
            road_image: 도로 이미지 (BGR)
            pothole_image: 포트홀 이미지 (BGR)
            position: 합성 위치 (x, y). None이면 랜덤
            scale: 포트홀 크기 스케일
            rotation: 회전 각도 (도)
            blend_mode: 블렌딩 모드 ("normal", "multiply", "overlay")
            
        Returns:
            (합성된 이미지, 바운딩 박스 좌표 (x1, y1, x2, y2))
        """
        # 포트홀 이미지 크기 조정
        pothole_h, pothole_w = pothole_image.shape[:2]
        new_width = int(pothole_w * scale)
        new_height = int(pothole_h * scale)
        pothole_resized = cv2.resize(pothole_image, (new_width, new_height))
        
        # 회전 적용
        if rotation != 0:
            center = (new_width // 2, new_height // 2)
            M = cv2.getRotationMatrix2D(center, rotation, 1.0)
            pothole_resized = cv2.warpAffine(pothole_resized, M, (new_width, new_height))
        
        # 위치 결정
        road_h, road_w = road_image.shape[:2]
        if position is None:
            # 랜덤 위치 (경계선 고려)
            margin = max(new_width, new_height) // 2
            x = random.randint(margin, road_w - new_width - margin)
            y = random.randint(margin, road_h - new_height - margin)
        else:
            x, y = position
            # 경계 체크 및 조정
            x = max(0, min(x, road_w - new_width))
            y = max(0, min(y, road_h - new_height))
        
        # 합성 영역 추출
        road_roi = road_image[y:y+new_height, x:x+new_width].copy()
        
        # 블렌딩 모드에 따른 합성
        if blend_mode == "normal":
            # 알파 블렌딩 (포트홀이 어두우므로 multiply 비슷하게)
            alpha = 0.7
            blended = cv2.addWeighted(road_roi, 1-alpha, pothole_resized, alpha, 0)
        elif blend_mode == "multiply":
            # Multiply 블렌딩 (더 자연스러운 그림자 효과)
            blended = np.clip((road_roi.astype(np.float32) * pothole_resized.astype(np.float32) / 255.0), 0, 255).astype(np.uint8)
        elif blend_mode == "overlay":
            # Overlay 블렌딩
            blended = self._overlay_blend(road_roi, pothole_resized)
        else:
            blended = pothole_resized
        
        # 합성 영역을 원본 이미지에 적용
        result = road_image.copy()
        result[y:y+new_height, x:x+new_width] = blended
        
        # 바운딩 박스 좌표 (YOLO 형식으로 나중에 변환)
        bbox = (x, y, x + new_width, y + new_height)
        
        return result, bbox
    
    def _overlay_blend(self, base: np.ndarray, overlay: np.ndarray) -> np.ndarray:
        """Overlay 블렌딩"""
        base_f = base.astype(np.float32) / 255.0
        overlay_f = overlay.astype(np.float32) / 255.0
        
        mask = base_f < 0.5
        result = np.where(mask, 
                         2 * base_f * overlay_f,
                         1 - 2 * (1 - base_f) * (1 - overlay_f))
        
        return np.clip(result * 255.0, 0, 255).astype(np.uint8)
    
    def convert_bbox_to_yolo(self, bbox: Tuple[int, int, int, int], img_width: int, img_height: int) -> Tuple[float, float, float, float]:
        """
        바운딩 박스를 YOLO 형식으로 변환
        
        Args:
            bbox: (x1, y1, x2, y2) 픽셀 좌표
            img_width: 이미지 너비
            img_height: 이미지 높이
            
        Returns:
            (center_x, center_y, width, height) 정규화된 좌표 (0-1 범위)
        """
        x1, y1, x2, y2 = bbox
        
        center_x = (x1 + x2) / 2.0 / img_width
        center_y = (y1 + y2) / 2.0 / img_height
        width = (x2 - x1) / img_width
        height = (y2 - y1) / img_height
        
        return (center_x, center_y, width, height)
    
    def save_yolo_label(self, label_path: str, class_id: int, yolo_bbox: Tuple[float, float, float, float]):
        """
        YOLO 형식 라벨 파일 저장
        
        Args:
            label_path: 라벨 파일 경로
            class_id: 클래스 ID (포트홀은 보통 0)
            yolo_bbox: YOLO 형식 바운딩 박스
        """
        os.makedirs(os.path.dirname(label_path), exist_ok=True)
        with open(label_path, 'w') as f:
            f.write(f"{class_id} {yolo_bbox[0]:.6f} {yolo_bbox[1]:.6f} {yolo_bbox[2]:.6f} {yolo_bbox[3]:.6f}\n")
    
    def generate_synthetic_dataset(self,
                                  road_images_dir: str,
                                  output_images_dir: str,
                                  output_labels_dir: str,
                                  num_potholes_per_image: int = 1,
                                  min_scale: float = 0.5,
                                  max_scale: float = 1.5,
                                  class_id: int = 0) -> Dict:
        """
        배치로 합성 데이터셋 생성
        
        Args:
            road_images_dir: 도로 이미지가 있는 디렉토리
            output_images_dir: 출력 이미지 디렉토리
            output_labels_dir: 출력 라벨 디렉토리
            num_potholes_per_image: 이미지당 포트홀 개수
            min_scale: 최소 스케일
            max_scale: 최대 스케일
            class_id: YOLO 클래스 ID
            
        Returns:
            생성 통계 딕셔너리
        """
        os.makedirs(output_images_dir, exist_ok=True)
        os.makedirs(output_labels_dir, exist_ok=True)
        
        # 도로 이미지 파일 목록
        road_image_files = [f for f in os.listdir(road_images_dir) 
                           if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        stats = {
            'total_images': len(road_image_files),
            'processed_images': 0,
            'total_potholes': 0,
            'failed': 0
        }
        
        for img_file in road_image_files:
            try:
                # 도로 이미지 로드
                road_img_path = os.path.join(road_images_dir, img_file)
                road_image = cv2.imread(road_img_path)
                if road_image is None:
                    print(f"이미지 로드 실패: {img_file}")
                    stats['failed'] += 1
                    continue
                
                road_h, road_w = road_image.shape[:2]
                result_image = road_image.copy()
                yolo_labels = []
                
                # 이미지당 여러 포트홀 생성
                for i in range(num_potholes_per_image):
                    # 포트홀 생성
                    pothole_size = (random.randint(100, 300), random.randint(100, 300))
                    pothole_image = self._generate_pothole_texture(pothole_size, "asphalt")
                    
                    # 랜덤 파라미터
                    scale = random.uniform(min_scale, max_scale)
                    rotation = random.uniform(-30, 30)
                    blend_mode = random.choice(["normal", "multiply", "overlay"])
                    
                    # 합성
                    result_image, bbox = self.composite_pothole_on_road(
                        result_image, pothole_image,
                        position=None,  # 랜덤 위치
                        scale=scale,
                        rotation=rotation,
                        blend_mode=blend_mode
                    )
                    
                    # YOLO 형식으로 변환
                    yolo_bbox = self.convert_bbox_to_yolo(bbox, road_w, road_h)
                    yolo_labels.append((class_id, yolo_bbox))
                    stats['total_potholes'] += 1
                
                # 결과 저장
                output_img_path = os.path.join(output_images_dir, img_file)
                cv2.imwrite(output_img_path, result_image)
                
                # 라벨 저장
                label_file = os.path.splitext(img_file)[0] + '.txt'
                label_path = os.path.join(output_labels_dir, label_file)
                with open(label_path, 'w') as f:
                    for class_id, yolo_bbox in yolo_labels:
                        f.write(f"{class_id} {yolo_bbox[0]:.6f} {yolo_bbox[1]:.6f} {yolo_bbox[2]:.6f} {yolo_bbox[3]:.6f}\n")
                
                stats['processed_images'] += 1
                print(f"처리 완료: {img_file} ({stats['processed_images']}/{stats['total_images']})")
                
            except Exception as e:
                print(f"오류 발생 ({img_file}): {str(e)}")
                stats['failed'] += 1
                import traceback
                traceback.print_exc()
        
        return stats


def main():
    """메인 함수 - 예제 사용"""
    import argparse
    
    parser = argparse.ArgumentParser(description="포트홀 합성 데이터셋 생성기")
    parser.add_argument('--road_images', type=str, required=True,
                       help='도로 이미지가 있는 디렉토리')
    parser.add_argument('--output_images', type=str, required=True,
                       help='출력 이미지 디렉토리')
    parser.add_argument('--output_labels', type=str, required=True,
                       help='출력 라벨 디렉토리')
    parser.add_argument('--num_potholes', type=int, default=1,
                       help='이미지당 포트홀 개수 (기본값: 1)')
    parser.add_argument('--min_scale', type=float, default=0.5,
                       help='최소 포트홀 크기 스케일 (기본값: 0.5)')
    parser.add_argument('--max_scale', type=float, default=1.5,
                       help='최대 포트홀 크기 스케일 (기본값: 1.5)')
    
    args = parser.parse_args()
    
    # 생성기 초기화
    generator = SyntheticPotholeGenerator()
    
    # 데이터셋 생성
    print("합성 데이터셋 생성 시작...")
    stats = generator.generate_synthetic_dataset(
        road_images_dir=args.road_images,
        output_images_dir=args.output_images,
        output_labels_dir=args.output_labels,
        num_potholes_per_image=args.num_potholes,
        min_scale=args.min_scale,
        max_scale=args.max_scale
    )
    
    print("\n=== 생성 완료 ===")
    print(f"총 이미지: {stats['total_images']}")
    print(f"처리된 이미지: {stats['processed_images']}")
    print(f"생성된 포트홀: {stats['total_potholes']}")
    print(f"실패: {stats['failed']}")


if __name__ == "__main__":
    main()


