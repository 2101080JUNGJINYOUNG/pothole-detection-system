"""
Depth Anything V2 NPU 추론 스크립트
RBLN NPU를 사용하여 깊이 추정을 수행합니다.
"""

import torch
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse

try:
    from optimum.rbln import RBLNDepthAnythingForDepthEstimation
    RBLN_AVAILABLE = True
except ImportError:
    RBLN_AVAILABLE = False
    print("Warning: optimum-rbln이 설치되지 않았습니다. pip install optimum-rbln을 실행하세요.")


def load_model(model_name="depth-anything-v2"):
    """
    Depth Anything V2 모델을 로드합니다.
    
    Args:
        model_name: 모델 이름 또는 경로
        
    Returns:
        로드된 모델
    """
    if not RBLN_AVAILABLE:
        raise ImportError("optimum-rbln이 설치되지 않았습니다. pip install optimum-rbln을 실행하세요.")
    
    print(f"모델 로딩 중: {model_name}")
    model = RBLNDepthAnythingForDepthEstimation.from_pretrained(model_name)
    print("모델 로딩 완료")
    return model


def preprocess_image(image_path, target_size=(518, 518)):
    """
    이미지를 전처리합니다.
    
    Args:
        image_path: 입력 이미지 경로
        target_size: 목표 이미지 크기
        
    Returns:
        전처리된 이미지 (PIL Image)
    """
    image = Image.open(image_path).convert("RGB")
    image = image.resize(target_size, Image.Resampling.LANCZOS)
    return image


def inference(model, image_path, output_path=None):
    """
    NPU를 사용하여 깊이 추정을 수행합니다.
    
    Args:
        model: 로드된 모델
        image_path: 입력 이미지 경로
        output_path: 출력 깊이 맵 저장 경로 (None이면 자동 생성)
        
    Returns:
        깊이 맵 (numpy array)
    """
    # 이미지 전처리
    image = preprocess_image(image_path)
    
    # 모델의 전처리 메서드 사용
    inputs = model.preprocess(image)
    
    print("NPU에서 추론 수행 중...")
    # NPU에서 추론 수행
    with torch.no_grad():
        outputs = model(**inputs)
    
    # 깊이 맵 추출
    depth_map = outputs.depth
    
    # numpy 배열로 변환
    if isinstance(depth_map, torch.Tensor):
        depth_map = depth_map.cpu().numpy()
    
    # 배치 차원 제거 (있는 경우)
    if len(depth_map.shape) == 4:
        depth_map = depth_map.squeeze(0)
    if len(depth_map.shape) == 3:
        depth_map = depth_map.squeeze(0)
    
    # 출력 경로가 지정되지 않은 경우 자동 생성
    if output_path is None:
        input_path = Path(image_path)
        output_path = input_path.parent / f"{input_path.stem}_depth.png"
    
    # 깊이 맵 저장
    plt.imsave(output_path, depth_map, cmap="viridis")
    print(f"깊이 맵 저장 완료: {output_path}")
    
    return depth_map


def main():
    parser = argparse.ArgumentParser(description="Depth Anything V2 NPU 추론")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="입력 이미지 경로"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="출력 깊이 맵 경로 (기본값: 입력 이미지와 같은 디렉토리에 저장)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="depth-anything-v2",
        help="모델 이름 또는 경로 (기본값: depth-anything-v2)"
    )
    
    args = parser.parse_args()
    
    # 모델 로드
    model = load_model(args.model)
    
    # 추론 수행
    depth_map = inference(model, args.input, args.output)
    
    print("추론 완료!")


if __name__ == "__main__":
    main()




