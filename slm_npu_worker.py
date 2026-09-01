"""
SLM NPU Worker
OpenVINO를 사용하여 NPU에서 Small Language Model을 실행하는 HTTP 서비스
"""

from flask import Flask, request, jsonify
import argparse
import os
import sys
from typing import Optional, Dict, List
import logging

# OpenVINO imports
try:
    from openvino import Core, Tensor
    from openvino.runtime import Type
    OPENVINO_AVAILABLE = True
except ImportError:
    OPENVINO_AVAILABLE = False
    print("Warning: OpenVINO가 설치되지 않았습니다.")

# Transformers for tokenization (SLM 모델용)
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: Transformers가 설치되지 않았습니다.")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SLMNPUWorker:
    """OpenVINO를 사용한 SLM NPU Worker"""
    
    def __init__(self, model_path: Optional[str] = None, device: str = "AUTO:NPU,CPU"):
        """
        Args:
            model_path: OpenVINO IR 모델 경로 (.xml 파일)
            device: 실행 디바이스 (AUTO:NPU,CPU, CPU, GPU 등)
        """
        self.core = None
        self.model = None
        self.compiled_model = None
        self.tokenizer = None
        self.device = device
        self.model_path = model_path
        
        if not OPENVINO_AVAILABLE:
            raise RuntimeError("OpenVINO가 설치되지 않았습니다.")
        
        # OpenVINO Core 초기화
        self.core = Core()
        
        # 모델이 제공되면 로드
        if model_path and os.path.exists(model_path):
            self.load_model(model_path, device)
    
    def load_model(self, model_path: str, device: str = None):
        """OpenVINO IR 모델 로드"""
        if device:
            self.device = device
        
        try:
            logger.info(f"모델 로드 중: {model_path}")
            logger.info(f"디바이스: {self.device}")
            
            # 모델 로드
            self.model = self.core.read_model(model_path)
            
            # 컴파일
            self.compiled_model = self.core.compile_model(
                self.model,
                device_name=self.device
            )
            
            # 입력/출력 레이어 정보
            self.input_layer = self.compiled_model.input(0)
            self.output_layer = self.compiled_model.output(0)
            
            logger.info("✅ 모델 로드 완료")
            logger.info(f"입력 레이어: {self.input_layer.get_names()}")
            logger.info(f"출력 레이어: {self.output_layer.get_names()}")
            
            # Tokenizer 로드 (모델 디렉토리에서)
            model_dir = os.path.dirname(model_path)
            tokenizer_path = os.path.join(model_dir, "tokenizer")
            if os.path.exists(tokenizer_path) and TRANSFORMERS_AVAILABLE:
                self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
                logger.info("✅ Tokenizer 로드 완료")
            else:
                logger.warning("Tokenizer를 찾을 수 없습니다. 기본 토크나이저를 사용합니다.")
            
            return True
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {str(e)}")
            raise
    
    def generate_response(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """
        프롬프트에 대한 응답 생성
        
        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 생성 토큰 수
            temperature: 생성 온도 (0.0-1.0)
            
        Returns:
            생성된 텍스트
        """
        if not self.compiled_model:
            raise RuntimeError("모델이 로드되지 않았습니다.")
        
        try:
            # Tokenizer로 입력 토큰화
            if self.tokenizer:
                inputs = self.tokenizer(prompt, return_tensors="np")
                input_ids = inputs["input_ids"]
            else:
                # 기본 토크나이저 (간단한 구현)
                # 실제로는 모델에 맞는 토크나이저 필요
                raise NotImplementedError("Tokenizer가 필요합니다.")
            
            # 추론 실행
            # OpenVINO IR 모델의 입력 형식에 맞게 조정 필요
            # 실제 구현은 모델 구조에 따라 다를 수 있음
            
            # 여기서는 예시 구조
            # 실제로는 모델의 입력/출력 형식에 맞게 구현해야 함
            output = self.compiled_model([input_ids])[self.output_layer]
            
            # 디코딩
            if self.tokenizer:
                generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
            else:
                generated_text = str(output)
            
            return generated_text
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            raise
    
    def is_model_loaded(self) -> bool:
        """모델이 로드되었는지 확인"""
        return self.compiled_model is not None


# 전역 worker 인스턴스
worker = None


@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': worker.is_model_loaded() if worker else False,
        'openvino_available': OPENVINO_AVAILABLE,
        'transformers_available': TRANSFORMERS_AVAILABLE,
        'model_path': worker.model_path if worker else None,
        'device': worker.device if worker else None
    })


@app.route('/load_model', methods=['POST'])
def load_model_endpoint():
    """모델 로드 엔드포인트"""
    global worker
    
    try:
        data = request.get_json()
        model_path = data.get('model_path')
        device = data.get('device', 'AUTO:NPU,CPU')
        
        if not model_path:
            return jsonify({
                'success': False,
                'error': 'model_path가 필요합니다.'
            }), 400
        
        if not os.path.exists(model_path):
            return jsonify({
                'success': False,
                'error': f'모델 파일을 찾을 수 없습니다: {model_path}'
            }), 404
        
        # Worker 초기화 또는 모델 재로드
        if worker is None:
            worker = SLMNPUWorker(model_path=model_path, device=device)
        else:
            worker.load_model(model_path, device)
        
        return jsonify({
            'success': True,
            'message': '모델 로드 완료',
            'model_path': model_path,
            'device': device
        })
        
    except Exception as e:
        logger.error(f"모델 로드 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """챗 엔드포인트"""
    global worker
    
    if worker is None or not worker.is_model_loaded():
        return jsonify({
            'success': False,
            'error': '모델이 로드되지 않았습니다. /load_model을 먼저 호출하세요.'
        }), 400
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        max_tokens = data.get('max_tokens', 200)
        temperature = data.get('temperature', 0.7)
        
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'prompt가 필요합니다.'
            }), 400
        
        # 응답 생성
        response_text = worker.generate_response(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return jsonify({
            'success': True,
            'response': response_text,
            'prompt': prompt
        })
        
    except Exception as e:
        logger.error(f"챗 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/models', methods=['GET'])
def list_available_models():
    """사용 가능한 디바이스 목록"""
    if not OPENVINO_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'OpenVINO가 설치되지 않았습니다.'
        }), 500
    
    try:
        core = Core()
        devices = core.available_devices
        
        return jsonify({
            'success': True,
            'devices': devices
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='SLM NPU Worker (OpenVINO)')
    parser.add_argument('--model', type=str, help='OpenVINO IR 모델 경로 (.xml)')
    parser.add_argument('--device', type=str, default='AUTO:NPU,CPU',
                       help='실행 디바이스 (기본값: AUTO:NPU,CPU)')
    parser.add_argument('--port', type=int, default=9002,
                       help='서버 포트 (기본값: 9002)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='서버 호스트 (기본값: 0.0.0.0)')
    
    args = parser.parse_args()
    
    global worker
    
    # 모델이 제공되면 초기 로드
    if args.model:
        try:
            worker = SLMNPUWorker(model_path=args.model, device=args.device)
            logger.info(f"✅ 초기 모델 로드 완료: {args.model}")
        except Exception as e:
            logger.error(f"초기 모델 로드 실패: {str(e)}")
            logger.info("런타임에 /load_model로 모델을 로드할 수 있습니다.")
    else:
        logger.info("모델 경로가 제공되지 않았습니다. 런타임에 /load_model로 로드하세요.")
    
    # 서버 시작
    logger.info(f"🚀 SLM NPU Worker 시작: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()


