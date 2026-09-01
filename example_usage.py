"""
Depth Anything V2 NPU 추론 예제 코드
간단한 사용 예제를 제공합니다.
"""

from inference_npu import load_model, inference
from pathlib import Path

def example_basic_usage():
    """기본 사용 예제"""
    print("=" * 50)
    print("Depth Anything V2 NPU 추론 예제")
    print("=" * 50)
    
    # 모델 로드
    model = load_model("depth-anything-v2")
    
    # 입력 이미지 경로 (사용자가 변경해야 함)
    input_image = "sample.jpg"
    
    # 이미지 파일이 존재하는지 확인
    if not Path(input_image).exists():
        print(f"경고: {input_image} 파일을 찾을 수 없습니다.")
        print("다른 이미지 경로를 지정하거나 이미지를 준비해주세요.")
        return
    
    # 추론 수행
    depth_map = inference(model, input_image)
    
    print(f"\n깊이 맵 크기: {depth_map.shape}")
    print(f"깊이 값 범위: [{depth_map.min():.4f}, {depth_map.max():.4f}]")
    print("\n추론 완료!")


if __name__ == "__main__":
    example_basic_usage()




