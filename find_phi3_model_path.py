"""
Phi-3 모델의 Hugging Face 캐시 경로 찾기
"""

import os
from pathlib import Path

def find_huggingface_cache(model_id: str = "microsoft/phi-3-mini-4k-instruct"):
    """Hugging Face 캐시에서 모델 경로 찾기"""
    
    # Hugging Face 캐시 기본 경로
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    
    # 모델 ID에서 경로 생성
    # microsoft/phi-3-mini-4k-instruct -> models--microsoft--phi-3-mini-4k-instruct
    model_path_name = model_id.replace("/", "--")
    model_cache_path = os.path.join(cache_dir, f"models--{model_path_name}")
    
    print(f"Hugging Face 캐시 디렉토리: {cache_dir}")
    print(f"모델 캐시 경로: {model_cache_path}")
    
    if os.path.exists(model_cache_path):
        print(f"\n✅ 모델 캐시를 찾았습니다!")
        
        # 실제 모델 파일이 있는 디렉토리 찾기
        # 캐시는 보통 snapshots/하위에 있음
        snapshots_dir = os.path.join(model_cache_path, "snapshots")
        if os.path.exists(snapshots_dir):
            # 가장 최신 snapshot 찾기
            snapshots = [d for d in os.listdir(snapshots_dir) if os.path.isdir(os.path.join(snapshots_dir, d))]
            if snapshots:
                latest_snapshot = sorted(snapshots)[-1]
                model_dir = os.path.join(snapshots_dir, latest_snapshot)
                print(f"모델 디렉토리: {model_dir}")
                
                # 필수 파일 확인
                required_files = ["config.json", "tokenizer.json", "model.safetensors.index.json"]
                if all(os.path.exists(os.path.join(model_dir, f)) for f in required_files):
                    print(f"\n✅ 완전한 모델 디렉토리를 찾았습니다!")
                    return model_dir
                else:
                    print(f"\n⚠️  일부 파일이 없습니다. 다운로드가 진행 중일 수 있습니다.")
        
        return model_cache_path
    else:
        print(f"\n❌ 모델 캐시를 찾을 수 없습니다.")
        print(f"모델을 먼저 다운로드해야 합니다:")
        print(f"  python -c \"from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('{model_id}')\"")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phi-3 모델의 Hugging Face 캐시 경로 찾기")
    parser.add_argument("--model", type=str, default="microsoft/phi-3-mini-4k-instruct",
                       help="Hugging Face 모델 ID")
    
    args = parser.parse_args()
    
    model_path = find_huggingface_cache(args.model)
    
    if model_path:
        print(f"\n{'='*60}")
        print(f"✅ 모델 경로: {model_path}")
        print(f"{'='*60}")
        print(f"\n사용 방법:")
        print(f"python slm_npu_worker_phi3.py --model {model_path} --device NPU --port 9002")


