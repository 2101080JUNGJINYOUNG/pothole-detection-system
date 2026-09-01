"""
SLM NPU Worker - Phi-3-mini with OpenVINO
OpenVINO GenAI를 사용하여 Phi-3-mini 모델을 NPU에서 실행하는 HTTP 서비스
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import argparse
import os
import sys
import logging
import threading
from typing import Optional, Dict

# OpenVINO GenAI imports
try:
    from openvino_genai import LLMPipeline
    OPENVINO_GENAI_AVAILABLE = True
except ImportError:
    OPENVINO_GENAI_AVAILABLE = False
    print("Warning: OpenVINO GenAI가 설치되지 않았습니다. pip install openvino-genai를 실행하세요.")

# OpenVINO Core for NPU configuration
try:
    from openvino import Core
    OPENVINO_CORE_AVAILABLE = True
except ImportError:
    OPENVINO_CORE_AVAILABLE = False

# NPU 전용 최적화: 환경 변수 초기화 (오히려 방해가 될 수 있으므로 제거)
import os
# 환경 변수는 Python 시작 전에 설정된 것만 사용, 여기서는 설정하지 않음

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phi3MiniNPUWorker:
    """OpenVINO GenAI를 사용한 Phi-3-mini NPU Worker"""
    
    def __init__(self, model_path: Optional[str] = None, device: str = "NPU"):
        """
        Args:
            model_path: 모델 경로 또는 Hugging Face 모델 ID
            device: 실행 디바이스 (NPU, CPU, AUTO 등)
        """
        self.pipeline = None
        self.device = device
        self.model_path = model_path or "microsoft/phi-3-mini-4k-instruct"
        self.available = OPENVINO_GENAI_AVAILABLE
        
        if self.available and model_path:
            try:
                self.load_model(model_path, device)
            except Exception as e:
                logger.error(f"초기 모델 로드 실패: {e}")
    
    def load_model(self, model_path: str = None, device: str = None):
        """Phi-3-mini 모델 로드 - NPU 전용 최적화"""
        if device:
            self.device = device
        if model_path:
            self.model_path = model_path
        
        if not self.available:
            raise RuntimeError("OpenVINO GenAI가 설치되지 않았습니다.")
        
        logger.info(f"Phi-3-mini 모델 로드 중: {self.model_path}")
        logger.info(f"요청 디바이스: {self.device}")
        
        # 사용 가능한 디바이스 확인
        available_devices_list = []
        if OPENVINO_CORE_AVAILABLE:
            try:
                ov_core = Core()
                available_devices_list = ov_core.available_devices
                logger.info(f"사용 가능한 OpenVINO 디바이스: {available_devices_list}")
            except Exception as core_error:
                logger.warning(f"OpenVINO Core 초기화 실패: {core_error}")
        
        # NPU → GPU → CPU 순서로 시도
        if self.device.upper() == "NPU":
            # 1단계: NPU 시도
            npu_devices = [d for d in available_devices_list if 'NPU' in d.upper()]
            if npu_devices:
                logger.info("1단계: NPU 디바이스로 모델 로드 시도")
                try:
                    self.pipeline = LLMPipeline(
                        models_path=self.model_path,
                        device="NPU"
                    )
                    logger.info("✅ NPU 디바이스로 모델 로드 성공!")
                    return True
                except Exception as npu_error:
                    error_str = str(npu_error)
                    logger.warning(f"NPU 디바이스 로드 실패: {error_str[:200]}")
                    logger.info("GPU 디바이스로 시도합니다...")
            else:
                logger.warning("NPU 디바이스를 찾을 수 없습니다. GPU로 시도합니다...")
            
            # 2단계: GPU 시도
            gpu_devices = [d for d in available_devices_list if 'GPU' in d.upper()]
            if gpu_devices:
                logger.info("2단계: GPU 디바이스로 모델 로드 시도")
                try:
                    self.pipeline = LLMPipeline(
                        models_path=self.model_path,
                        device="GPU"
                    )
                    logger.info("✅ GPU 디바이스로 모델 로드 성공!")
                    self.device = "GPU"
                    return True
                except Exception as gpu_error:
                    error_str = str(gpu_error)
                    logger.warning(f"GPU 디바이스 로드 실패: {error_str[:200]}")
                    logger.info("CPU 디바이스로 폴백합니다...")
            else:
                logger.warning("GPU 디바이스를 찾을 수 없습니다. CPU로 폴백합니다...")
            
            # 3단계: CPU 폴백
            logger.info("3단계: CPU 디바이스로 모델 로드 시도 (최종 폴백)")
            self.device = "CPU"
        elif self.device.upper() == "GPU":
            # GPU 직접 요청
            logger.info("GPU 디바이스로 모델 로드 시도")
            try:
                self.pipeline = LLMPipeline(
                    models_path=self.model_path,
                    device="GPU"
                )
                logger.info("✅ GPU 디바이스로 모델 로드 성공!")
                return True
            except Exception as gpu_error:
                logger.warning(f"GPU 디바이스 로드 실패: {gpu_error}")
                logger.info("CPU 디바이스로 폴백합니다...")
                self.device = "CPU"
        
        # CPU 또는 다른 디바이스
        logger.info(f"CPU 디바이스로 모델 로드 시도")
        self.pipeline = LLMPipeline(
            models_path=self.model_path,
            device="CPU"
        )
        logger.info("✅ CPU 디바이스로 모델 로드 완료")
        return True
    
    def generate_response(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """
        프롬프트에 대한 응답 생성
        
        Args:
            prompt: 입력 프롬프트 (이미 포맷팅된 프롬프트 또는 일반 텍스트)
            max_tokens: 최대 생성 토큰 수
            temperature: 생성 온도 (0.0-1.0)
            
        Returns:
            생성된 텍스트
        """
        if not self.pipeline:
            raise RuntimeError("모델이 로드되지 않았습니다.")
        
        try:
            # 프롬프트가 이미 포맷팅되었는지 확인
            # <|system|> 태그가 있으면 이미 포맷팅된 것으로 간주
            if "<|system|>" not in prompt and "<|user|>" not in prompt:
                # 일반 텍스트인 경우 포맷팅
                formatted_prompt = self.format_prompt(prompt)
            else:
                # 이미 포맷팅된 경우 그대로 사용
                formatted_prompt = prompt
            
            # 생성 옵션
            generate_kwargs = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
            }
            
            # 추론 실행
            response = self.pipeline.generate(
                formatted_prompt,
                **generate_kwargs
            )
            
            # 응답 추출 (마크다운 형식 제거 가능)
            return response.strip()
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            raise
    
    def format_prompt(self, user_message: str, system_message: str = None) -> str:
        """
        Phi-3-mini용 프롬프트 포맷팅
        
        Phi-3-mini는 특별한 프롬프트 형식을 사용합니다:
        <|system|>{system_message}<|end|>
        <|user|>{user_message}<|end|>
        <|assistant|>
        """
        if system_message is None:
            system_message = "You are a helpful assistant."
        
        formatted = f"<|system|>\n{system_message}<|end|>\n<|user|>\n{user_message}<|end|>\n<|assistant|>\n"
        return formatted
    
    def is_model_loaded(self) -> bool:
        """모델이 로드되었는지 확인"""
        return self.pipeline is not None


# 전역 worker 인스턴스
worker = None
# 동시 요청 방지를 위한 Lock
generate_lock = threading.Lock()


@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': worker.is_model_loaded() if worker else False,
        'openvino_genai_available': OPENVINO_GENAI_AVAILABLE,
        'model_path': worker.model_path if worker else None,
        'device': worker.device if worker else None
    })


@app.route('/load_model', methods=['POST'])
def load_model_endpoint():
    """모델 로드 엔드포인트"""
    global worker
    
    try:
        data = request.get_json()
        model_path = data.get('model_path', 'microsoft/phi-3-mini-4k-instruct')
        device = data.get('device', 'NPU')
        
        # Worker 초기화 또는 모델 재로드
        if worker is None:
            worker = Phi3MiniNPUWorker(model_path=model_path, device=device)
        else:
            worker.load_model(model_path, device)
        
        return jsonify({
            'success': True,
            'message': 'Phi-3-mini 모델 로드 완료',
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
        system_message = data.get('system_message', None)
        max_tokens = data.get('max_tokens', 200)
        temperature = data.get('temperature', 0.7)
        
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'prompt가 필요합니다.'
            }), 400
        
        # 시스템 메시지가 제공되면 사용
        if system_message:
            formatted_prompt = worker.format_prompt(prompt, system_message)
        else:
            formatted_prompt = worker.format_prompt(prompt)
        
        # 동시 요청 방지 (Lock 사용)
        with generate_lock:
            # 응답 생성
            response_text = worker.generate_response(
                formatted_prompt,
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


@app.route('/devices', methods=['GET'])
def list_available_devices():
    """사용 가능한 디바이스 목록"""
    try:
        from openvino import Core
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
    parser = argparse.ArgumentParser(description='Phi-3-mini SLM NPU Worker (OpenVINO GenAI)')
    parser.add_argument('--model', type=str, default='microsoft/phi-3-mini-4k-instruct',
                       help='모델 경로 또는 Hugging Face 모델 ID (기본값: microsoft/phi-3-mini-4k-instruct)')
    parser.add_argument('--device', type=str, default='NPU',
                       help='실행 디바이스 (NPU, CPU, GPU, AUTO - 기본값: NPU)')
    parser.add_argument('--port', type=int, default=9002,
                       help='서버 포트 (기본값: 9002)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='서버 호스트 (기본값: 0.0.0.0)')
    
    args = parser.parse_args()
    
    global worker
    
    if not OPENVINO_GENAI_AVAILABLE:
        logger.error("OpenVINO GenAI가 설치되지 않았습니다.")
        logger.info("설치 방법: pip install openvino-genai")
        sys.exit(1)
    
    # Worker 초기화
    try:
        worker = Phi3MiniNPUWorker(model_path=args.model, device=args.device)
        logger.info(f"✅ Phi-3-mini 모델 로드 완료: {args.model}")
        logger.info(f"✅ 디바이스: {args.device}")
    except Exception as e:
        logger.error(f"초기 모델 로드 실패: {str(e)}")
        logger.info("런타임에 /load_model로 모델을 로드할 수 있습니다.")
    
    # 서버 시작
    logger.info(f"🚀 Phi-3-mini SLM NPU Worker 시작: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()

