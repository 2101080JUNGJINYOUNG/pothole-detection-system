"""
Phi-3-mini Chatbot for LAMP Container
OpenVINO GenAI를 사용한 Phi-3-mini 챗봇 클래스
"""

import os
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

# OpenVINO GenAI imports
try:
    from openvino_genai import LLMPipeline
    OPENVINO_GENAI_AVAILABLE = True
except ImportError:
    OPENVINO_GENAI_AVAILABLE = False
    print("Warning: OpenVINO GenAI가 설치되지 않았습니다.")

# OpenVINO Core for NPU configuration
try:
    from openvino import Core
    OPENVINO_CORE_AVAILABLE = True
except ImportError:
    OPENVINO_CORE_AVAILABLE = False

logger = logging.getLogger(__name__)

# 프로젝트 컨텍스트 정보
PROJECT_CONTEXT = """
## Deep-Guardian 프로젝트 개요
Deep-Guardian은 AI 기반 포트홀 탐지 및 모니터링 시스템입니다.

## 시스템 구조
1. AI Core: YOLOv8로 포트홀 탐지 → NPU Worker로 깊이 검증 → DB 저장
2. Dashboard: 웹 대시보드 (데이터 시각화, 관리)
3. Database: MySQL (포트홀 데이터 저장)

## 데이터베이스 필드 의미
- depth_ratio (깊이 비율): 0.0~1.0, 깊이 맵에서 0.3 이상인 픽셀 비율. 0.1 이상이면 검증 통과 (validation_result=True)
- confidence_score: YOLOv8 탐지 신뢰도 (0.0~1.0)
- validation_result: 검증 결과 (True/False). depth_ratio >= 0.1이면 True
- risk_level: 위험도 등급 ('critical', 'high', 'medium', 'low')
- priority_score: 우선순위 점수 (높을수록 더 위험/우선)
"""


class Phi3Chatbot:
    """OpenVINO GenAI를 사용한 Phi-3-mini 챗봇"""
    
    def __init__(self, model_path: Optional[str] = None, device: str = "NPU"):
        """
        Args:
            model_path: 모델 경로 또는 Hugging Face 모델 ID
            device: 실행 디바이스 (NPU, GPU, CPU)
        """
        self.pipeline = None
        self.device = device
        self.model_path = model_path or os.getenv('PHI3_MODEL_PATH', '/app/models/llm/Phi-3-mini-int4')
        self.available = OPENVINO_GENAI_AVAILABLE
        
        if self.available and model_path:
            try:
                self.load_model(model_path, device)
            except Exception as e:
                logger.error(f"초기 모델 로드 실패: {e}")
    
    def load_model(self, model_path: str = None, device: str = None):
        """Phi-3-mini 모델 로드"""
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
            npu_devices = [d for d in available_devices_list if 'NPU' in d.upper()]
            if npu_devices:
                try:
                    self.pipeline = LLMPipeline(models_path=self.model_path, device="NPU")
                    logger.info("✅ NPU 디바이스로 모델 로드 성공!")
                    return True
                except Exception as e:
                    logger.warning(f"NPU 로드 실패: {e}, GPU로 시도...")
            
            gpu_devices = [d for d in available_devices_list if 'GPU' in d.upper()]
            if gpu_devices:
                try:
                    self.pipeline = LLMPipeline(models_path=self.model_path, device="GPU")
                    logger.info("✅ GPU 디바이스로 모델 로드 성공!")
                    self.device = "GPU"
                    return True
                except Exception as e:
                    logger.warning(f"GPU 로드 실패: {e}, CPU로 폴백...")
            
            self.device = "CPU"
        
        # CPU 또는 다른 디바이스
        logger.info(f"CPU 디바이스로 모델 로드 시도")
        self.pipeline = LLMPipeline(models_path=self.model_path, device="CPU")
        logger.info("✅ CPU 디바이스로 모델 로드 완료")
        return True
    
    def format_prompt(self, user_message: str, system_message: str = None) -> str:
        """Phi-3-mini용 프롬프트 포맷팅"""
        if system_message is None:
            system_message = f"""You are a helpful assistant for the Deep-Guardian road pothole detection system.
{PROJECT_CONTEXT}
Answer questions about potholes, road safety, and the system in Korean."""
        
        formatted = f"<|system|>\n{system_message}<|end|>\n<|user|>\n{user_message}<|end|>\n<|assistant|>\n"
        return formatted
    
    def generate_response(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """프롬프트에 대한 응답 생성"""
        if not self.pipeline:
            raise RuntimeError("모델이 로드되지 않았습니다.")
        
        try:
            # 프롬프트 포맷팅
            if "<|system|>" not in prompt and "<|user|>" not in prompt:
                formatted_prompt = self.format_prompt(prompt)
            else:
                formatted_prompt = prompt
            
            # 생성 옵션
            generate_kwargs = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
            }
            
            # 추론 실행
            response = self.pipeline.generate(formatted_prompt, **generate_kwargs)
            return response.strip()
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            raise
    
    def is_model_loaded(self) -> bool:
        """모델이 로드되었는지 확인"""
        return self.pipeline is not None


# 전역 챗봇 인스턴스
phi3_chatbot = None

def get_chatbot():
    """챗봇 인스턴스 가져오기 (지연 로딩)"""
    global phi3_chatbot
    if phi3_chatbot is None:
        model_path = os.getenv('PHI3_MODEL_PATH', '/app/models/llm/Phi-3-mini-int4')
        device = os.getenv('PHI3_DEVICE', 'NPU')
        try:
            phi3_chatbot = Phi3Chatbot(model_path=model_path, device=device)
            if not phi3_chatbot.is_model_loaded():
                phi3_chatbot.load_model(model_path, device)
        except Exception as e:
            logger.error(f"챗봇 초기화 실패: {e}")
            phi3_chatbot = None
    return phi3_chatbot

