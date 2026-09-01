"""
NPU Worker 테스트 스크립트
로컬에서 NPU Worker 서버를 테스트합니다.
"""

import requests
import json
from pathlib import Path

def test_health_check(base_url="http://localhost:9001"):
    """헬스 체크 테스트"""
    print("=" * 50)
    print("헬스 체크 테스트")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/health")
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"에러: {str(e)}")
        return False


def test_depth_inference(image_path, base_url="http://localhost:9001"):
    """깊이 추정 테스트"""
    print("\n" + "=" * 50)
    print("깊이 추정 테스트")
    print("=" * 50)
    
    if not Path(image_path).exists():
        print(f"에러: 이미지 파일을 찾을 수 없습니다: {image_path}")
        return False
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(f"{base_url}/depth", files=files)
        
        print(f"상태 코드: {response.status_code}")
        result = response.json()
        print(f"응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('success'):
            print(f"\n깊이 비율: {result.get('depth_ratio', 0):.4f}")
            print(f"검증 결과: {'통과' if result.get('validation_result') else '실패'}")
            return True
        else:
            print(f"에러: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="NPU Worker 테스트")
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:9001",
        help="NPU Worker 서버 URL"
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="테스트할 이미지 경로"
    )
    
    args = parser.parse_args()
    
    # 헬스 체크
    health_ok = test_health_check(args.url)
    
    if not health_ok:
        print("\n경고: 서버가 응답하지 않습니다. 서버가 실행 중인지 확인하세요.")
        return
    
    # 깊이 추정 테스트
    if args.image:
        test_depth_inference(args.image, args.url)
    else:
        print("\n이미지 경로가 지정되지 않았습니다. --image 옵션으로 이미지 경로를 지정하세요.")
        print("예: python test_npu_worker.py --image sample.jpg")


if __name__ == "__main__":
    main()




