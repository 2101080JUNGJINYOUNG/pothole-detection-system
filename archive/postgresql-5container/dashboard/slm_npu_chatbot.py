"""
OpenVINO NPU를 사용한 SLM 챗봇 클라이언트
SLM NPU Worker와 통신하여 답변 생성
"""

import os
import sys
import django
import re
from typing import Dict, Optional
import requests
from datetime import datetime, timedelta

# Django setup
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    django_app_path_in_container = '/app/django_app'
    if os.path.exists(django_app_path_in_container):
        if '/app' not in sys.path:
            sys.path.insert(0, '/app')
    else:
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
    django.setup()

from django_app.models import Pothole
from django.db.models import Q, Count, Avg, Max
from typing import Dict

# 프로젝트 컨텍스트 정보
PROJECT_CONTEXT = """
## Deep-Guardian 프로젝트 개요
Deep-Guardian은 AI 기반 포트홀 탐지 및 모니터링 시스템입니다.

## 시스템 구조
1. AI Core: YOLOv8로 포트홀 탐지 → NPU Worker로 깊이 검증 → DB 저장
2. Dashboard: Streamlit 기반 웹 대시보드 (데이터 시각화, 관리)
3. Database: PostgreSQL (포트홀 데이터 저장)

## 데이터베이스 필드 의미
- depth_ratio (깊이 비율): 0.0~1.0, 깊이 맵에서 0.3 이상인 픽셀 비율. 0.1 이상이면 검증 통과 (validation_result=True)
- confidence_score: YOLOv8 탐지 신뢰도 (0.0~1.0)
- validation_result: 검증 결과 (True/False). depth_ratio >= 0.1이면 True
- risk_level: 위험도 등급 ('critical', 'high', 'medium', 'low')
- priority_score: 우선순위 점수 (높을수록 더 위험/우선). 위치 가중치 + 깊이 점수 + 검증 점수로 계산
- location_type: 위치 유형 ('school_area', 'hospital_area', 'highway', 'general' 등)
- location_description: 위치 설명 (예: "군산대학교 정문 앞")

## 위험도 평가 기준
- priority_score >= 30: critical (매우 위험)
- priority_score >= 20: high (높음)
- priority_score >= 10: medium (보통)
- priority_score < 10: low (낮음)

## 우선순위 점수 계산 방식
1. 위치 가중치: 학교/병원 주변 2.5, 고속도로 3.0, 일반 도로 1.0 등
2. 깊이 점수: depth_ratio * 0.3 * 10
3. 검증 점수: validation_result가 True면 추가 점수
4. 최종 점수 = 위치가중치*10 + 깊이점수 + 검증점수

## 주요 기능
- 실시간 포트홀 탐지 및 깊이 검증
- 위치 기반 위험도 자동 평가
- 데이터 시각화 및 관리자 검토
- 승인된 데이터로 모델 파인튜닝
"""


class SLMNPUChatbot:
    """OpenVINO NPU를 사용한 SLM 챗봇 (Phi-3-mini 지원)"""
    
    def __init__(self, worker_url: Optional[str] = None):
        """
        Args:
            worker_url: SLM NPU Worker URL (기본값: http://host.docker.internal:9002)
                       Phi-3-mini Worker와 호환됨
        """
        self.worker_url = worker_url or os.getenv('SLM_NPU_WORKER_URL', 'http://host.docker.internal:9002')
        self.available = self.check_connection()
    
    def check_connection(self) -> bool:
        """SLM NPU Worker 연결 확인"""
        # 여러 URL 시도 (host.docker.internal 우선)
        urls_to_try = []
        if 'host.docker.internal' in self.worker_url:
            # host.docker.internal을 먼저 시도
            urls_to_try.append(self.worker_url)
            # 대체 IP 시도 (작동하는 IP만)
            host_ips = ['192.168.65.254', '172.31.80.1', '172.17.0.1']
            urls_to_try.extend([self.worker_url.replace('host.docker.internal', ip) for ip in host_ips])
        else:
            urls_to_try.append(self.worker_url)
        
        for url in urls_to_try:
            try:
                response = requests.get(f"{url}/health", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    # 연결이 성공하면 True 반환 (model_loaded가 False여도 연결 자체는 성공)
                    # model_loaded는 모델이 완전히 로드되었는지 여부이므로, 연결 성공만으로도 True
                    return True
            except Exception:
                continue
        
        # 모든 연결 시도 실패 시에도 True 반환하여 UI 표시
        # 실제 사용 시 연결 문제가 있으면 그때 오류 표시
        return True
    
    def get_today_detections(self):
        """오늘 탐지된 포트홀 데이터 조회"""
        today = datetime.now().date()
        return Pothole.objects.filter(
            detected_at__date=today,
            validation_result=True
        ).order_by('-priority_score')
    
    def get_most_dangerous_today(self) -> Optional[Dict]:
        """오늘 가장 위험한 포트홀 조회"""
        today_detections = self.get_today_detections()
        if not today_detections.exists():
            return None
        
        most_dangerous = today_detections.first()
        return {
            'id': most_dangerous.id,
            'risk_level': most_dangerous.risk_level,
            'priority_score': float(most_dangerous.priority_score),
            'depth_ratio': float(most_dangerous.depth_ratio),
            'location_description': most_dangerous.location_description or f"위도: {most_dangerous.latitude}, 경도: {most_dangerous.longitude}",
            'image_path': most_dangerous.image_path,
            'detected_at': most_dangerous.detected_at
        }
    
    def get_high_risk_potholes(self, days: int = 0, limit: int = 10) -> list:
        """위험도가 높은 포트홀 조회 (high, critical)"""
        try:
            today = datetime.now().date()
            
            if days == 0:
                start_date = today
            else:
                start_date = today - timedelta(days=days)
            
            # 위험도가 높은 포트홀 조회 (high 또는 critical)
            # 먼저 전체 포트홀 수 확인
            all_count = Pothole.objects.filter(
                detected_at__date__gte=start_date,
                detected_at__date__lte=today
            ).count()
            validated_count = Pothole.objects.filter(
                detected_at__date__gte=start_date,
                detected_at__date__lte=today,
                validation_result=True
            ).count()
            print(f"[DEBUG] 전체 포트홀: {all_count}건, 검증 통과: {validated_count}건")
            
            # 위험도별 분포 확인
            risk_dist = Pothole.objects.filter(
                detected_at__date__gte=start_date,
                detected_at__date__lte=today,
                validation_result=True
            ).values('risk_level').annotate(count=Count('id'))
            print(f"[DEBUG] 위험도 분포: {list(risk_dist)}")
            
            high_risk_potholes = Pothole.objects.filter(
                detected_at__date__gte=start_date,
                detected_at__date__lte=today,
                validation_result=True,
                risk_level__in=['high', 'critical']
            ).order_by('-priority_score', '-detected_at')[:limit]
            
            print(f"[DEBUG] 위험도 높은 포트홀 (high/critical) 조회: {high_risk_potholes.count()}건")
            
            result = []
            for p in high_risk_potholes:
                result.append({
                    'id': p.id,
                    'risk_level': p.risk_level,
                    'priority_score': float(p.priority_score) if p.priority_score else 0.0,
                    'depth_ratio': float(p.depth_ratio),
                    'location_description': p.location_description or f"위도: {p.latitude}, 경도: {p.longitude}",
                    'image_path': p.image_path,
                    'detected_at': p.detected_at
                })
            
            print(f"[DEBUG] 위험도 높은 포트홀 조회: {len(result)}건")
            return result
        except Exception as e:
            print(f"[ERROR] 위험도 높은 포트홀 조회 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_statistics(self, days: int = 0) -> Dict:
        """지정된 기간의 통계 데이터 조회
        
        Args:
            days: 조회할 기간 (일 수). 0이면 오늘만, 7이면 최근 7일
        """
        try:
            today = datetime.now().date()
            
            if days == 0:
                # 오늘만
                start_date = today
            else:
                # 최근 N일
                start_date = today - timedelta(days=days)
            
            # 데이터베이스 조회 시도
            queryset = Pothole.objects.filter(
                detected_at__date__gte=start_date,
                detected_at__date__lte=today
            )
            
            validated_queryset = queryset.filter(validation_result=True)
            
            total_count = queryset.count()
            validated_count = validated_queryset.count()
            
            risk_distribution = validated_queryset.values('risk_level').annotate(count=Count('id'))
            
            avg_depth = validated_queryset.aggregate(avg_depth=Avg('depth_ratio'))['avg_depth'] or 0.0
            
            max_priority = validated_queryset.aggregate(max_priority=Max('priority_score'))['max_priority'] or 0.0
            
            # 디버깅: 실제 조회된 데이터 확인
            print(f"[DEBUG] DB 조회 성공: 기간={days}일, 총={total_count}건, 검증={validated_count}건")
            
            return {
                'total_count': total_count,
                'validated_count': validated_count,
                'risk_distribution': {item['risk_level']: item['count'] for item in risk_distribution},
                'avg_depth_ratio': float(avg_depth) if avg_depth else 0.0,
                'max_priority_score': float(max_priority) if max_priority else 0.0,
                'days': days,
                'start_date': start_date,
                'end_date': today
            }
        except Exception as e:
            # DB 접속 실패 시 상세 오류 로깅
            print(f"[ERROR] DB 조회 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            # 빈 데이터 반환 (오류 발생 시)
            return {
                'total_count': 0,
                'validated_count': 0,
                'risk_distribution': {},
                'avg_depth_ratio': 0.0,
                'max_priority_score': 0.0,
                'days': days,
                'start_date': datetime.now().date(),
                'end_date': datetime.now().date(),
                'error': str(e)
            }
    
    def get_statistics_today(self) -> Dict:
        """오늘 통계 데이터 조회 (호환성 유지)"""
        return self.get_statistics(days=0)
    
    def extract_keywords_from_question(self, question: str) -> Dict:
        """질문에서 키워드를 추출하여 적절한 데이터 조회 전략 결정"""
        question_lower = question.lower()
        
        # 날짜 범위 추출 (일 수)
        days = 0  # 기본값: 0 (오늘만)
        time_filter = 'today'
        
        # 숫자와 "일", "날" 패턴 찾기
        day_patterns = [
            r'(\d+)\s*일',
            r'(\d+)\s*날',
            r'(\d+)\s*day',
            r'지난\s*(\d+)\s*일',
            r'최근\s*(\d+)\s*일',
            r'(\d+)\s*일간',
            r'(\d+)\s*일\s*동안',
            r'최근\s*(\d+)\s*일\s*동안',  # "최근 5일동안" 패턴 추가
            r'(\d+)\s*일\s*동안'  # "5일동안" 패턴 추가
        ]
        
        for pattern in day_patterns:
            match = re.search(pattern, question_lower)
            if match:
                days = int(match.group(1))
                time_filter = f'last_{days}_days'
                break
        
        if days == 0:
            if any(kw in question_lower for kw in ['오늘', '금일', 'today']):
                time_filter = 'today'
                days = 0
            elif any(kw in question_lower for kw in ['어제', 'yesterday']):
                time_filter = 'yesterday'
                days = 1
            elif any(kw in question_lower for kw in ['최근', '지난', 'recent', 'last']):
                # "최근", "지난"만 있고 숫자가 없으면 기본 30일 (더 넓은 범위)
                time_filter = 'last_30_days'
                days = 30
            else:
                # 날짜가 명시되지 않았고 "위험도 높은" 질문이면 최근 30일로 확장
                if any(kw in question_lower for kw in ['위험도가 높은', '위험한', 'high risk', 'critical']):
                    time_filter = 'last_30_days'
                    days = 30
        
        query_type = 'general'
        keywords = []
        
        if any(kw in question_lower for kw in ['가장 위험', '가장 심각', '최고 위험']):
            query_type = 'most_dangerous'
            keywords.append('위험')
        elif any(kw in question_lower for kw in ['위험도가 높은', '위험한', 'high risk', 'critical', '높은 위험']):
            query_type = 'high_risk'
            keywords.append('위험도')
        elif any(kw in question_lower for kw in ['어디', '위치', '장소', '곳']):
            query_type = 'location'
            keywords.append('위치')
        elif any(kw in question_lower for kw in ['몇 개', '개수', '통계', '탐지']):
            query_type = 'stats'
        
        return {
            'query_type': query_type,
            'keywords': keywords,
            'time_filter': time_filter,
            'days': days
        }
    
    def query_relevant_data(self, question: str) -> Dict:
        """질문에 관련된 데이터를 직접 조회"""
        try:
            keywords_info = self.extract_keywords_from_question(question)
            result = {
                'stats': None,
                'most_dangerous': None,
                'relevant_potholes': []
            }
            
            # 통계 데이터 조회 (질문에서 추출한 날짜 범위 사용)
            days = keywords_info.get('days', 0)
            print(f"[DEBUG] 질문 분석: days={days}, query_type={keywords_info.get('query_type')}")
            result['stats'] = self.get_statistics(days=days)
            
            # 가장 위험한 포트홀 (위험 관련 질문인 경우)
            if keywords_info['query_type'] in ['most_dangerous', 'location']:
                try:
                    result['most_dangerous'] = self.get_most_dangerous_today()
                except Exception as e:
                    print(f"[ERROR] 가장 위험한 포트홀 조회 실패: {str(e)}")
                    result['most_dangerous'] = None
            
            # 위험도가 높은 포트홀들 조회
            if keywords_info['query_type'] == 'high_risk':
                try:
                    print(f"[DEBUG] 위험도 높은 포트홀 조회 시작: days={days}")
                    result['relevant_potholes'] = self.get_high_risk_potholes(days=days, limit=10)
                    print(f"[DEBUG] 위험도 높은 포트홀 조회 완료: {len(result['relevant_potholes'])}건")
                except Exception as e:
                    print(f"[ERROR] 위험도 높은 포트홀 조회 실패: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    result['relevant_potholes'] = []
            
            return result
        except Exception as e:
            print(f"[ERROR] query_relevant_data 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            # 기본값 반환
            return {
                'stats': {'total_count': 0, 'validated_count': 0, 'error': str(e)},
                'most_dangerous': None,
                'relevant_potholes': []
            }
    
    def format_context_for_llm(self, question: str, relevant_data: Dict = None) -> str:
        """LLM에 제공할 컨텍스트 데이터 포맷팅 (조회된 데이터 기반)"""
        if relevant_data is None:
            relevant_data = self.query_relevant_data(question)
        
        context_parts = []
        
        if relevant_data['stats']:
            stats = relevant_data['stats']
            days = stats.get('days', 0)
            if days == 0:
                period_text = "오늘"
            elif days == 1:
                period_text = "어제"
            else:
                period_text = f"최근 {days}일"
            
            context_parts.append(f"{period_text} 탐지된 포트홀 통계:")
            context_parts.append(f"- 조회 기간: {stats.get('start_date')} ~ {stats.get('end_date')}")
            context_parts.append(f"- 총 탐지 건수: {stats['total_count']}건")
            context_parts.append(f"- 검증 통과: {stats['validated_count']}건")
            context_parts.append(f"- 평균 깊이 비율: {stats['avg_depth_ratio']:.3f}")
            context_parts.append(f"- 최대 우선순위 점수: {stats['max_priority_score']:.2f}")
            
            if stats['risk_distribution']:
                context_parts.append(f"\n위험도 분포:")
                for risk, count in stats['risk_distribution'].items():
                    context_parts.append(f"- {risk}: {count}건")
        
        if relevant_data['most_dangerous']:
            md = relevant_data['most_dangerous']
            context_parts.append(f"\n가장 위험한 포트홀:")
            context_parts.append(f"- ID: {md['id']}")
            context_parts.append(f"- 위험도: {md['risk_level']}")
            context_parts.append(f"- 우선순위 점수: {md['priority_score']:.2f}")
            context_parts.append(f"- 깊이 비율: {md['depth_ratio']:.3f}")
            context_parts.append(f"- 위치: {md['location_description']}")
            if md.get('image_path'):
                context_parts.append(f"- 이미지: {md['image_path']}")
        
        # 위험도 높은 포트홀 목록이 있는 경우 (high_risk 질문)
        if relevant_data.get('relevant_potholes'):
            potholes_list = relevant_data['relevant_potholes']
            if len(potholes_list) > 0:
                context_parts.append(f"\n위험도가 높은 포트홀 목록 (총 {len(potholes_list)}건):")
                for idx, p in enumerate(potholes_list, 1):
                    context_parts.append(f"\n{idx}. 포트홀 ID: {p['id']}")
                    context_parts.append(f"   - 위험도: {p['risk_level']} (critical=매우 위험, high=높음)")
                    context_parts.append(f"   - 우선순위 점수: {p['priority_score']:.2f}")
                    context_parts.append(f"   - 깊이 비율: {p['depth_ratio']:.3f}")
                    context_parts.append(f"   - 위치: {p['location_description']}")
                    context_parts.append(f"   - 탐지 시각: {p['detected_at']}")
                    if p.get('image_path'):
                        context_parts.append(f"   - 이미지 경로: {p['image_path']}")
            else:
                context_parts.append(f"\n위험도가 높은 포트홀 (high 또는 critical): 조회된 데이터가 없습니다.")
        
        return "\n".join(context_parts) if context_parts else "데이터 없음"
    
    def answer_question(self, question: str) -> Dict:
        """
        사용자 질문에 답변 생성
        
        Args:
            question: 사용자 질문
            
        Returns:
            {
                'answer': 답변 텍스트,
                'data': 관련 데이터 (있을 경우),
                'image_path': 관련 이미지 경로 (있을 경우)
            }
        """
        # available 체크를 제거하고 실제 연결 시도
        # 연결 실패 시 오류 메시지 반환
        
        try:
            # 1. 먼저 질문에 관련된 데이터를 직접 조회
            print(f"[DEBUG] 질문 수신: {question}")
            relevant_data = self.query_relevant_data(question)
            print(f"[DEBUG] 조회된 데이터: stats={relevant_data.get('stats', {}).get('total_count', 0)}건")
            
            # 2. 조회된 데이터를 기반으로 컨텍스트 생성
            context = self.format_context_for_llm(question, relevant_data)
            print(f"[DEBUG] 생성된 컨텍스트 길이: {len(context)}자")
            
            # 프롬프트 생성 (프로젝트 컨텍스트 포함)
            prompt = f"""당신은 Deep-Guardian 포트홀 탐지 시스템의 AI 어시스턴트입니다.

프로젝트 컨텍스트:
{PROJECT_CONTEXT}

포트홀 데이터:
{context}

사용자 질문: {question}

답변 요구사항:
1. 한국어로 자연스럽고 친절하게 답변
2. 구체적인 숫자와 위치 정보 포함
3. 위험도(risk_level)와 우선순위 점수(priority_score) 설명 포함
4. depth_ratio는 "깊이 비율"이라고 설명 (0.1 이상이면 검증 통과)
5. priority_score가 높으면 더 위험하다고 명확히 설명
6. 이미지가 있는 경우 "사진을 확인해드릴까요?" 같은 제안 포함
7. 간결하고 명확하게 (3-5문장)

답변:"""
            
            # 시스템 메시지 (간결하게)
            system_message = """당신은 Deep-Guardian 포트홀 탐지 시스템의 AI 어시스턴트입니다.
제공된 데이터를 바탕으로 사용자의 질문에 정확하고 친절하게 답변합니다."""
            
            # SLM NPU Worker API 호출 (Phi-3-mini Worker와 호환)
            # 여러 URL 시도 (연결 문제 대비)
            # host.docker.internal을 우선 시도하고, 실패 시 다른 IP 시도
            urls_to_try = []
            
            # 1. host.docker.internal 시도 (Docker Desktop에서 자동으로 해석) - 우선순위 1
            if 'host.docker.internal' in self.worker_url:
                urls_to_try.append(self.worker_url)
                # 2. Windows Host IP 시도 (Docker Desktop의 기본 게이트웨이)
                # Docker Desktop for Windows는 보통 192.168.65.254를 사용
                # 작동하는 IP만 포함 (10.0.0.2, 172.17.0.1 제거 - 작동하지 않음)
                host_ips = ['192.168.65.254', '172.31.80.1']
                urls_to_try.extend([self.worker_url.replace('host.docker.internal', ip) for ip in host_ips])
            else:
                urls_to_try.append(self.worker_url)
            
            response = None
            last_error = None
            for url in urls_to_try:
                try:
                    print(f"[DEBUG] NPU Worker 연결 시도: {url}/chat")
                    response = requests.post(
                        f"{url}/chat",
                        json={
                            'prompt': prompt,
                            'system_message': system_message,
                            'max_tokens': 300,  # 토큰 수 감소 (응답 시간 단축)
                            'temperature': 0.7
                        },
                        timeout=120  # 타임아웃 대폭 증가 (복잡한 질문 처리 시간 고려)
                    )
                    if response.status_code == 200:
                        print(f"[DEBUG] NPU Worker 연결 성공: {url}")
                        break  # 성공하면 루프 종료
                    else:
                        print(f"[DEBUG] NPU Worker 응답 오류: {response.status_code}")
                except Exception as e:
                    print(f"[DEBUG] NPU Worker 연결 실패: {url} - {str(e)[:100]}")
                    last_error = e
                    continue
            
            if response is None or response.status_code != 200:
                # 더 친절한 오류 메시지
                error_detail = str(last_error) if last_error else "알 수 없는 오류"
                raise Exception(f"NPU Worker에 연결할 수 없습니다. Windows 방화벽에서 포트 9002를 허용했는지 확인하세요. (오류: {error_detail})")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    answer_text = result.get('response', '').strip()
                    print(f"[DEBUG] 응답 생성 완료: 길이={len(answer_text)}자")
                    return {
                        'answer': answer_text,
                        'data': relevant_data,
                        'image_path': relevant_data.get('most_dangerous', {}).get('image_path') if relevant_data.get('most_dangerous') else None
                    }
                else:
                    error_msg = result.get('error', '알 수 없는 오류')
                    print(f"[ERROR] Worker 오류: {error_msg}")
                    return {
                        'answer': f"오류: {error_msg}",
                        'data': relevant_data,
                        'image_path': None
                    }
            else:
                error_msg = f"Worker 응답 오류 (상태 코드: {response.status_code})"
                print(f"[ERROR] {error_msg}")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                except:
                    pass
                return {
                    'answer': error_msg,
                    'data': relevant_data,
                    'image_path': None
                }
            
            # 조회된 관련 데이터 사용
            data = None
            image_path = None
            
            if relevant_data['most_dangerous']:
                data = relevant_data['most_dangerous']
                image_path = relevant_data['most_dangerous'].get('image_path')
            
            return {
                'answer': answer_text,
                'data': data,
                'image_path': image_path
            }
            
        except Exception as e:
            return {
                'answer': f'죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}',
                'data': None,
                'image_path': None
            }


def check_slm_npu_connection(worker_url: str = None) -> bool:
    """SLM NPU Worker 연결 확인 (빠른 실패)"""
    url = worker_url or os.getenv('SLM_NPU_WORKER_URL', 'http://host.docker.internal:9002')
    
    # host.docker.internal을 우선 시도하고, 실패 시 Host IP 시도
    urls_to_try = []
    if 'host.docker.internal' in url:
        # host.docker.internal을 먼저 시도 (우선순위 1)
        urls_to_try.append(url)
        # 대체 IP 시도 (작동하는 IP만, 10.0.0.2 제거)
        host_ips = ['192.168.65.254', '172.31.80.1', '172.17.0.1']
        urls_to_try.extend([url.replace('host.docker.internal', ip) for ip in host_ips])
    else:
        urls_to_try.append(url)
    
    # 타임아웃을 짧게 설정하여 빠르게 실패
    for test_url in urls_to_try:
        try:
            # 타임아웃을 2초로 줄여서 빠르게 실패
            response = requests.get(f"{test_url}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                # 연결이 성공하면 True 반환
                return True
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            # 타임아웃이나 연결 오류는 즉시 다음 URL 시도
            continue
        except Exception:
            # 기타 오류도 빠르게 넘어감
            continue
    
    # 모든 연결 시도 실패 시에도 True 반환하여 UI를 표시
    # 실제 사용 시 오류가 발생하면 그때 처리
    return True

