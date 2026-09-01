"""
고급 챗봇 기능 (데이터베이스 컨텍스트 통합)
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from django_app.models import Pothole
from django.db.models import Q, Count, Avg, Max
from phi3_chatbot import get_chatbot

PROJECT_CONTEXT = """
## Deep-Guardian 프로젝트 개요
Deep-Guardian은 AI 기반 포트홀 탐지 및 모니터링 시스템입니다.

## 시스템 구조
1. AI Core: YOLOv8로 포트홀 탐지 → NPU Worker로 깊이 검증 → DB 저장
2. Dashboard: 웹 대시보드 (데이터 시각화, 관리)
3. Database: MySQL (포트홀 데이터 저장)

## 데이터베이스 필드 의미
- depth_ratio (깊이 비율): 0.0~1.0, 깊이 맵에서 0.3 이상인 픽셀 비율. 0.1 이상이면 검증 통과
- confidence_score: YOLOv8 탐지 신뢰도 (0.0~1.0)
- validation_result: 검증 결과 (True/False). depth_ratio >= 0.1이면 True
- risk_level: 위험도 등급 ('critical', 'high', 'medium', 'low')
- priority_score: 우선순위 점수 (높을수록 더 위험/우선)
- location_type: 위치 유형 ('school_area', 'hospital_area', 'highway', 'general' 등)
"""

class AdvancedChatbot:
    """고급 챗봇 (데이터베이스 컨텍스트 통합)"""
    
    def __init__(self):
        self.chatbot = get_chatbot()
    
    def get_today_detections(self):
        """오늘 탐지된 포트홀 데이터 조회"""
        today = datetime.now().date()
        return Pothole.objects.filter(
            detected_at__date=today,
            validation_result=True
        ).order_by('-priority_score')
    
    def get_statistics(self, days=0):
        """통계 데이터 조회"""
        today = datetime.now().date()
        start_date = today - timedelta(days=days) if days > 0 else today
        
        queryset = Pothole.objects.filter(
            detected_at__date__gte=start_date,
            detected_at__date__lte=today,
            validation_result=True
        )
        
        stats = queryset.aggregate(
            total_count=Count('id'),
            avg_depth=Avg('depth_ratio'),
            max_priority=Max('priority_score')
        )
        
        risk_dist = queryset.values('risk_level').annotate(
            count=Count('id')
        )
        
        return {
            'total_count': stats['total_count'] or 0,
            'avg_depth': float(stats['avg_depth']) if stats['avg_depth'] else 0.0,
            'max_priority': float(stats['max_priority']) if stats['max_priority'] else 0.0,
            'risk_distribution': list(risk_dist)
        }
    
    def get_high_risk_potholes(self, days=0, limit=10):
        """위험도가 높은 포트홀 조회"""
        today = datetime.now().date()
        start_date = today - timedelta(days=days) if days > 0 else today
        
        potholes = Pothole.objects.filter(
            detected_at__date__gte=start_date,
            detected_at__date__lte=today,
            validation_result=True,
            risk_level__in=['high', 'critical']
        ).order_by('-priority_score')[:limit]
        
        return [{
            'id': p.id,
            'risk_level': p.risk_level,
            'priority_score': float(p.priority_score) if p.priority_score else 0.0,
            'depth_ratio': float(p.depth_ratio),
            'location_description': p.location_description or f"위도: {p.latitude}, 경도: {p.longitude}"
        } for p in potholes]
    
    def extract_keywords(self, question: str) -> Dict:
        """질문에서 키워드 추출"""
        keywords = {
            'today': '오늘' in question or 'today' in question.lower(),
            'statistics': '통계' in question or 'statistics' in question.lower(),
            'dangerous': '위험' in question or 'dangerous' in question.lower(),
            'count': '개수' in question or 'count' in question.lower(),
            'location': '위치' in question or 'location' in question.lower()
        }
        return keywords
    
    def query_relevant_data(self, question: str) -> Dict:
        """질문과 관련된 데이터 조회"""
        keywords = self.extract_keywords(question)
        data = {}
        
        if keywords['today'] or keywords['statistics']:
            days = 7 if '7일' in question or '일주일' in question else 0
            data['statistics'] = self.get_statistics(days=days)
        
        if keywords['dangerous']:
            days = 7 if '7일' in question or '일주일' in question else 0
            data['high_risk'] = self.get_high_risk_potholes(days=days, limit=5)
        
        if keywords['today']:
            data['today_detections'] = list(self.get_today_detections()[:10].values(
                'id', 'depth_ratio', 'priority_score', 'risk_level', 'location_description'
            ))
        
        return data
    
    def format_context(self, question: str, relevant_data: Dict = None) -> str:
        """컨텍스트 포맷팅"""
        if relevant_data is None:
            relevant_data = self.query_relevant_data(question)
        
        context = PROJECT_CONTEXT + "\n\n## 현재 데이터베이스 상태\n\n"
        
        if 'statistics' in relevant_data:
            stats = relevant_data['statistics']
            context += f"- 전체 탐지 수: {stats['total_count']}개\n"
            context += f"- 평균 깊이 비율: {stats['avg_depth']:.3f}\n"
            context += f"- 최대 우선순위 점수: {stats['max_priority']:.1f}\n"
        
        if 'high_risk' in relevant_data:
            context += f"\n- 위험도 높은 포트홀: {len(relevant_data['high_risk'])}개\n"
        
        if 'today_detections' in relevant_data:
            context += f"\n- 오늘 탐지된 포트홀: {len(relevant_data['today_detections'])}개\n"
        
        return context
    
    def answer_question(self, question: str) -> Dict:
        """질문에 대한 답변 생성"""
        if not self.chatbot or not self.chatbot.is_model_loaded():
            return {
                'success': False,
                'error': '챗봇 모델이 로드되지 않았습니다'
            }
        
        try:
            # 관련 데이터 조회
            relevant_data = self.query_relevant_data(question)
            
            # 컨텍스트 포맷팅
            context = self.format_context(question, relevant_data)
            
            # 프롬프트 생성
            system_message = f"""You are a helpful assistant for the Deep-Guardian road pothole detection system.
{context}

Answer questions about potholes, road safety, and the system in Korean. Use the provided data to give accurate answers."""
            
            prompt = f"{system_message}\n\n사용자 질문: {question}"
            
            # 응답 생성
            response = self.chatbot.generate_response(prompt, max_tokens=300, temperature=0.7)
            
            return {
                'success': True,
                'response': response,
                'context_used': bool(relevant_data)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# 전역 인스턴스
advanced_chatbot = None

def get_advanced_chatbot():
    """고급 챗봇 인스턴스 가져오기"""
    global advanced_chatbot
    if advanced_chatbot is None:
        advanced_chatbot = AdvancedChatbot()
    return advanced_chatbot

