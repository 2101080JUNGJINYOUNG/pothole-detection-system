"""
Deep-Guardian NPU Worker (Windows Host)
OpenVINO를 사용하여 Depth Anything V2 모델로 깊이 추정을 수행하는 HTTP 서비스

엔드포인트: http://host.docker.internal:9001/depth
입력: 이미지 파일 (multipart/form-data)
출력: JSON {depth_ratio, depth_map, validation_result}
"""

import os
import io
import json
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2

try:
    from openvino import Core
    OPENVINO_AVAILABLE = True
except ImportError:
    OPENVINO_AVAILABLE = False
    print("Warning: OpenVINO가 설치되지 않았습니다.")

app = Flask(__name__)
CORS(app)  # Docker 컨테이너에서 접근 가능하도록 CORS 활성화

# 전역 변수
ov_core = None
compiled_model = None
input_layer = None
output_layer = None
MODEL_PATH = None


def load_openvino_model(model_xml_path, device="AUTO:NPU,GPU,CPU"):
    """
    OpenVINO IR 모델을 로드하고 컴파일합니다.
    
    Args:
        model_xml_path: OpenVINO IR 모델 XML 파일 경로
        device: 사용할 디바이스 (기본값: AUTO:NPU,GPU,CPU - NPU 우선)
        
    Returns:
        compiled_model, input_layer, output_layer
    """
    global ov_core, compiled_model, input_layer, output_layer, MODEL_PATH
    
    if not OPENVINO_AVAILABLE:
        raise ImportError("OpenVINO가 설치되지 않았습니다.")
    
    print(f"OpenVINO 모델 로딩 중: {model_xml_path}")
    print(f"사용 디바이스: {device}")
    
    # OpenVINO Core 초기화
    ov_core = Core()
    
    # 사용 가능한 디바이스 확인
    available_devices = ov_core.available_devices
    print(f"사용 가능한 디바이스: {available_devices}")
    
    # 모델 로드
    model = ov_core.read_model(model_xml_path)
    
    # 모델 컴파일
    print(f"모델 컴파일 중... (디바이스: {device})")
    compiled_model = ov_core.compile_model(model, device)
    
    # 입력/출력 레이어 정보 가져오기
    input_layer = compiled_model.input(0)
    output_layer = compiled_model.output(0)
    
    print(f"입력 레이어: {input_layer.get_shape()}")
    print(f"출력 레이어: {output_layer.get_shape()}")
    print("모델 로딩 완료")
    
    # 모델 경로 저장
    MODEL_PATH = model_xml_path
    
    return compiled_model, input_layer, output_layer


def preprocess_image(image, target_size=(518, 518)):
    """
    이미지를 모델 입력 형식으로 전처리합니다.
    
    Args:
        image: PIL Image 또는 numpy array
        target_size: 목표 이미지 크기 (width, height)
        
    Returns:
        전처리된 이미지 (numpy array, shape: [1, 3, H, W])
    """
    if isinstance(image, Image.Image):
        image = np.array(image)
    
    # RGB로 변환 (BGR인 경우)
    if len(image.shape) == 3 and image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 리사이즈
    image = cv2.resize(image, target_size, interpolation=cv2.INTER_LINEAR)
    
    # 정규화 (ImageNet 통계)
    image = image.astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    image = (image - mean) / std
    
    # [H, W, C] -> [C, H, W]
    image = np.transpose(image, (2, 0, 1))
    
    # 배치 차원 추가 [1, C, H, W]
    image = np.expand_dims(image, axis=0)
    
    return image.astype(np.float32)


def postprocess_depth(depth_map):
    """
    깊이 맵을 후처리합니다.
    
    Args:
        depth_map: 모델 출력 깊이 맵
        
    Returns:
        후처리된 깊이 맵 (numpy array)
    """
    # 배치 차원 제거
    if len(depth_map.shape) == 4:
        depth_map = depth_map.squeeze(0)
    if len(depth_map.shape) == 3:
        depth_map = depth_map.squeeze(0)
    
    # 정규화 (0-1 범위로)
    depth_min = depth_map.min()
    depth_max = depth_map.max()
    if depth_max > depth_min:
        depth_map = (depth_map - depth_min) / (depth_max - depth_min)
    
    return depth_map


def calculate_depth_ratio(depth_map, threshold=0.3):
    """
    깊이 맵에서 깊은 영역의 비율을 계산합니다.
    
    Args:
        depth_map: 깊이 맵 (numpy array)
        threshold: 깊은 영역으로 판단할 임계값 (0-1)
        
    Returns:
        depth_ratio: 깊은 영역의 비율
    """
    # 임계값보다 깊은 영역 찾기
    deep_pixels = (depth_map > threshold).sum()
    total_pixels = depth_map.size
    
    depth_ratio = deep_pixels / total_pixels if total_pixels > 0 else 0.0
    
    return float(depth_ratio)


def validate_pothole_depth(depth_ratio, min_depth_ratio=0.1):
    """
    포트홀 깊이 검증을 수행합니다.
    
    Args:
        depth_ratio: 깊은 영역의 비율
        min_depth_ratio: 최소 깊이 비율 임계값
        
    Returns:
        validation_result: 검증 통과 여부 (bool)
    """
    return depth_ratio >= min_depth_ratio


@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        "status": "healthy",
        "model_loaded": compiled_model is not None,
        "openvino_available": OPENVINO_AVAILABLE,
        "model_path": MODEL_PATH if MODEL_PATH else None
    })


@app.route('/load_model', methods=['POST'])
def load_model_endpoint():
    """
    런타임에 모델을 로드하는 엔드포인트
    
    입력:
        - JSON {
            "model_path": "경로/to/openvino_model.xml",
            "device": "AUTO:NPU,CPU" (선택)
          }
    """
    global compiled_model, input_layer, output_layer, MODEL_PATH
    
    if not OPENVINO_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "OpenVINO가 설치되지 않았습니다."
        }), 500
    
    try:
        data = request.get_json()
        if not data or 'model_path' not in data:
            return jsonify({
                "success": False,
                "error": "model_path가 필요합니다."
            }), 400
        
        model_path = data['model_path']
        device = data.get('device', 'AUTO:NPU,GPU,CPU')
        
        if not os.path.exists(model_path):
            return jsonify({
                "success": False,
                "error": f"모델 파일을 찾을 수 없습니다: {model_path}"
            }), 404
        
        # 모델 로드
        load_openvino_model(model_path, device)
        MODEL_PATH = model_path
        
        return jsonify({
            "success": True,
            "message": "모델 로드 완료",
            "model_path": model_path,
            "device": device
        })
        
    except Exception as e:
        print(f"모델 로드 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/depth', methods=['POST'])
def depth_inference():
    """
    깊이 추정 엔드포인트
    
    입력:
        - multipart/form-data로 이미지 파일 전송
        - 필드명: 'image'
        
    출력:
        - JSON {
            "success": bool,
            "depth_ratio": float,
            "validation_result": bool,
            "depth_map_shape": [int, int],
            "message": str
          }
    """
    global compiled_model, input_layer, output_layer
    
    if compiled_model is None:
        return jsonify({
            "success": False,
            "error": "모델이 로드되지 않았습니다."
        }), 500
    
    try:
        # 이미지 파일 받기
        if 'image' not in request.files:
            return jsonify({
                "success": False,
                "error": "이미지 파일이 없습니다. 'image' 필드로 전송해주세요."
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "파일이 선택되지 않았습니다."
            }), 400
        
        # 이미지 로드
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # 전처리
        input_tensor = preprocess_image(image)
        
        # 추론 수행
        print("NPU에서 추론 수행 중...")
        result = compiled_model([input_tensor])
        depth_map = result[output_layer]
        
        # 후처리
        depth_map = postprocess_depth(depth_map)
        
        # 깊이 비율 계산
        depth_ratio = calculate_depth_ratio(depth_map)
        
        # 검증 수행
        validation_result = validate_pothole_depth(depth_ratio)
        
        return jsonify({
            "success": True,
            "depth_ratio": depth_ratio,
            "validation_result": validation_result,
            "depth_map_shape": list(depth_map.shape),
            "depth_min": float(depth_map.min()),
            "depth_max": float(depth_map.max()),
            "message": "추론 완료"
        })
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deep-Guardian NPU Worker")
    parser.add_argument(
        "--model",
        type=str,
        default="openvino_model.xml",
        help="OpenVINO IR 모델 XML 파일 경로"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="AUTO:NPU,GPU,CPU",
        help="사용할 디바이스 (기본값: AUTO:NPU,GPU,CPU - NPU 우선)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9001,
        help="서버 포트 (기본값: 9001)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="서버 호스트 (기본값: 0.0.0.0)"
    )
    
    args = parser.parse_args()
    
    # 모델 경로 확인 및 검색
    model_found = False
    if os.path.exists(args.model):
        model_found = True
    else:
        print(f"경고: 모델 파일을 찾을 수 없습니다: {args.model}")
        print("다른 경로에서 모델을 찾는 중...")
        
        # 검색할 경로 목록
        search_paths = [
            args.model,  # 원본 경로
            os.path.join(os.getcwd(), args.model),  # 현재 디렉토리
            os.path.join(os.path.dirname(os.getcwd()), args.model),  # 상위 디렉토리
            os.path.join(os.getcwd(), "models", args.model),  # models 서브디렉토리
            os.path.join(os.getcwd(), "model", args.model),  # model 서브디렉토리
        ]
        
        # 사용자 홈 디렉토리에서도 검색
        home_paths = [
            os.path.join(os.path.expanduser("~"), "Desktop", args.model),
            os.path.join(os.path.expanduser("~"), "Documents", args.model),
        ]
        search_paths.extend(home_paths)
        
        for path in search_paths:
            if os.path.exists(path):
                args.model = path
                model_found = True
                print(f"모델 파일을 찾았습니다: {path}")
                break
    
    # 모델 로드 시도
    if model_found:
        try:
            load_openvino_model(args.model, args.device)
            MODEL_PATH = args.model
            print(f"모델 로드 성공: {MODEL_PATH}")
        except Exception as e:
            print(f"모델 로드 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            print("서버는 시작되지만 모델이 로드되지 않았습니다.")
            print("서버 시작 후 /load_model 엔드포인트로 모델을 로드할 수 있습니다.")
    else:
        print("=" * 50)
        print("모델 파일을 찾을 수 없습니다.")
        print("=" * 50)
        print("서버는 모델 없이 시작됩니다.")
        print("다음 방법으로 모델을 로드할 수 있습니다:")
        print("1. 서버 재시작 시 --model 옵션으로 모델 경로 지정")
        print("2. POST /load_model 엔드포인트 사용")
        print("=" * 50)
    
    # 서버 시작
    print(f"\n{'='*50}")
    print(f"Deep-Guardian NPU Worker 시작")
    print(f"{'='*50}")
    print(f"호스트: {args.host}")
    print(f"포트: {args.port}")
    print(f"엔드포인트: http://{args.host}:{args.port}/depth")
    print(f"{'='*50}\n")
    
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()

