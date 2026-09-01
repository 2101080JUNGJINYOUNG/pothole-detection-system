"""
모델 로드 예제 스크립트
서버가 실행 중일 때 모델을 로드하는 예제
"""

import requests
import json
import sys

def load_model(server_url="http://localhost:9001", model_path=None):
    """
    서버에 모델을 로드합니다.
    
    Args:
        server_url: NPU Worker 서버 URL
        model_path: OpenVINO IR 모델 XML 파일 경로
    """
    if model_path is None:
        print("사용법: python load_model_example.py <모델_경로>")
        print("예시: python load_model_example.py C:\\path\\to\\openvino_model.xml")
        return False
    
    import os
    if not os.path.exists(model_path):
        print(f"에러: 모델 파일을 찾을 수 없습니다: {model_path}")
        return False
    
    # 절대 경로로 변환
    model_path = os.path.abspath(model_path)
    
    print(f"모델 로드 요청: {model_path}")
    
    try:
        payload = {
            "model_path": model_path,
            "device": "AUTO:NPU,CPU"
        }
        
        response = requests.post(
            f"{server_url}/load_model",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"상태 코드: {response.status_code}")
        result = response.json()
        print(f"응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('success'):
            print("\n모델 로드 성공!")
            return True
        else:
            print(f"\n모델 로드 실패: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else None
    load_model(model_path=model_path)




