"""
Deep-Guardian Streamlit 대시보드
포트홀 데이터 시각화 및 관리
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time
import os
import json
import io
import base64
import cv2
import sys
import django

# Django setup
django_app_path_in_container = '/app/django_app'  # Docker 컨테이너에서 마운트된 경로
if os.path.exists(django_app_path_in_container):
    # Docker 컨테이너 환경 - /app이 이미 sys.path에 있을 수 있지만 확실히 하기 위해 추가
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')
else:
    # 로컬 환경
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
django.setup()

from django_app.models import Pothole
from django.db.models import Count, Avg, Max, Q, F
from auth import check_authentication, is_admin, login_page, logout
from video_results_page import video_results_page
# NPU + Phi-3-mini만 사용 (Ollama, Gemini 제거)
try:
    from slm_npu_chatbot import SLMNPUChatbot, check_slm_npu_connection
    SLM_NPU_AVAILABLE = True
except ImportError:
    SLM_NPU_AVAILABLE = False
    def check_slm_npu_connection():
        return False

# 페이지 설정
st.set_page_config(
    page_title="Deep-Guardian Dashboard",
    page_icon="🕳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Django ORM을 사용하므로 별도 연결 불필요

@st.cache_data(ttl=5)  # 5초 캐싱으로 데이터베이스 부하 감소
def get_potholes(limit=100):
    """포트홀 데이터 조회 using Django ORM"""
    try:
        potholes = Pothole.objects.filter(
            approved_for_training=True
        ).order_by('-priority_score', '-detected_at')[:limit]
        
        # Convert to DataFrame
        data = []
        for p in potholes:
            data.append({
                'id': p.id,
                'latitude': float(p.latitude),
                'longitude': float(p.longitude),
                'depth_ratio': float(p.depth_ratio),
                'validation_result': p.validation_result,
                'detected_at': p.detected_at,
                'image_path': p.image_path,
                'location_type': p.location_type,
                'risk_level': p.risk_level,
                'priority_score': float(p.priority_score) if p.priority_score else 0.0,
                'location_description': p.location_description
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"데이터 조회 오류: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=5)  # 5초 캐싱으로 데이터베이스 부하 감소
def get_statistics():
    """통계 데이터 조회 using Django ORM"""
    try:
        from django.db.models import Avg, Max
        from django.db.models.functions import Coalesce
        
        stats = Pothole.objects.filter(
            approved_for_training=True
        ).aggregate(
            total_count=Count('id'),
            validated_count=Count('id', filter=Q(validation_result=True)),
            avg_depth_ratio=Avg('depth_ratio'),
            last_detection=Max('detected_at')
        )
        
        # Convert to dict format similar to previous version
        result = {
            'total_count': stats['total_count'] or 0,
            'validated_count': stats['validated_count'] or 0,
            'avg_depth_ratio': float(stats['avg_depth_ratio']) if stats['avg_depth_ratio'] else 0.0,
            'last_detection': stats['last_detection']
        }
        
        return pd.Series(result)
    except Exception as e:
        st.error(f"통계 조회 오류: {str(e)}")
        return None

# 관리자 이미지 검토 페이지
def admin_review_page():
    """관리자 전용: 포트홀 이미지 검토 및 파인튜닝 데이터 선정"""
    st.title("🔍 관리자: 포트홀 이미지 검토")
    
    # 필터 옵션
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        review_status = st.selectbox(
            "검토 상태",
            ["전체", "검토 대기", "승인됨", "거부됨"],
            index=0,
            key="review_status_filter"
        )
    with col2:
        validation_status = st.selectbox(
            "검증 상태",
            ["전체", "검증됨", "미검증"],
            index=0,
            key="validation_status_filter"
        )
    with col3:
        limit = st.number_input("표시 개수", min_value=10, max_value=100, value=20, step=10, key="limit_filter")
    with col4:
        st.write("")  # 공간 확보
        st.write("")  # 공간 확보
        if st.button("🔄 새로고침", use_container_width=True, key="refresh_review_page"):
            st.cache_data.clear()
            st.rerun()
    
    # Django ORM으로 쿼리 구성
    try:
        queryset = Pothole.objects.all()  # select_related 제거 (reviewed_by는 property로 처리)
        
        # 필터 적용
        if review_status == "검토 대기":
            queryset = queryset.filter(approved_for_training__isnull=True)
        elif review_status == "승인됨":
            queryset = queryset.filter(approved_for_training=True)
        elif review_status == "거부됨":
            queryset = queryset.filter(approved_for_training=False)
        
        if validation_status == "검증됨":
            queryset = queryset.filter(validation_result=True)
        elif validation_status == "미검증":
            queryset = queryset.filter(validation_result=False)
        
        potholes = queryset.order_by('-detected_at')[:limit]
        
        if not potholes:
            st.info("검토할 이미지가 없습니다.")
            return
        
        st.write(f"**총 {len(potholes)}개의 이미지**")
        
        # 이미지별 검토
        for p in potholes:
            with st.container():
                st.divider()
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # 이미지 표시
                    if p.image_path:
                        # 이미지 경로 확인
                        img_path = p.image_path
                        if not os.path.isabs(img_path):
                            img_path = f"/app/shared_images/{os.path.basename(img_path)}"
                        elif not os.path.exists(img_path):
                            img_path = f"/app/shared_images/{os.path.basename(p.image_path)}"
                        
                        if os.path.exists(img_path):
                            try:
                                img = cv2.imread(img_path)
                                if img is not None:
                                    # 바운딩 박스 그리기
                                    if p.bbox_x1 and p.bbox_y1 and p.bbox_x2 and p.bbox_y2:
                                        cv2.rectangle(img, (p.bbox_x1, p.bbox_y1), (p.bbox_x2, p.bbox_y2), (0, 255, 0), 2)
                                    
                                    # BGR to RGB
                                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                    st.image(img_rgb, use_container_width=True, caption=f"포트홀 ID: {p.id}")
                            except Exception as e:
                                st.error(f"이미지 로드 실패: {str(e)}")
                        else:
                            st.warning(f"이미지 파일을 찾을 수 없습니다: {img_path}")
                    else:
                        st.info("이미지 경로가 없습니다.")
                
                with col2:
                    st.subheader(f"포트홀 ID: {p.id}")
                    
                    # 정보 표시
                    info_col1, info_col2 = st.columns(2)
                    with info_col1:
                        st.metric("깊이 비율", f"{float(p.depth_ratio):.3f}")
                        st.metric("신뢰도", f"{float(p.confidence_score):.3f}" if p.confidence_score else "N/A")
                    with info_col2:
                        st.metric("검증 결과", "✅ 검증됨" if p.validation_result else "❌ 미검증")
                        st.metric("검토 상태", 
                                 "✅ 승인" if p.approved_for_training is True else 
                                 "❌ 거부" if p.approved_for_training is False else "⏳ 대기")
                    
                    st.write(f"**위치**: {float(p.latitude):.6f}, {float(p.longitude):.6f}")
                    st.write(f"**탐지 시간**: {p.detected_at}")
                    
                    if p.reviewed_at:
                        st.write(f"**검토 시간**: {p.reviewed_at}")
                        if p.reviewed_by:
                            st.write(f"**검토자**: {p.reviewed_by.username}")
                    
                    if p.review_notes:
                        st.write(f"**검토 메모**: {p.review_notes}")
                    
                    # 검토 액션
                    st.write("---")
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if st.button("✅ 승인", key=f"approve_{p.id}", use_container_width=True):
                            if approve_pothole(p.id, st.session_state.user['id'], True):
                                st.success(f"포트홀 #{p.id} 승인 완료")
                                time.sleep(0.3)
                                st.cache_data.clear()
                                st.rerun()
                    
                    with action_col2:
                        if st.button("❌ 거부", key=f"reject_{p.id}", use_container_width=True):
                            if approve_pothole(p.id, st.session_state.user['id'], False):
                                st.success(f"포트홀 #{p.id} 거부 완료")
                                time.sleep(0.3)
                                st.cache_data.clear()
                                st.rerun()
                    
                    with action_col3:
                        if st.button("🔄 초기화", key=f"reset_{p.id}", use_container_width=True):
                            if approve_pothole(p.id, st.session_state.user['id'], None):
                                st.success(f"포트홀 #{p.id} 검토 상태 초기화 완료")
                                time.sleep(0.3)
                                st.cache_data.clear()
                                st.rerun()
                    
                    # 검토 메모
                    review_note = st.text_area(
                        "검토 메모",
                        value=p.review_notes or "",
                        key=f"note_{p.id}",
                        height=100
                    )
                    if st.button("💾 메모 저장", key=f"save_note_{p.id}"):
                        save_review_note(p.id, review_note)
                        st.success("메모가 저장되었습니다.")
    except Exception as e:
        st.error(f"데이터 조회 오류: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def approve_pothole(pothole_id, reviewer_id, approved):
    """포트홀 승인/거부 using Django ORM"""
    try:
        from django_app.models import User
        pothole = Pothole.objects.get(id=pothole_id)
        reviewer = User.objects.get(id=reviewer_id)
        
        pothole.approved_for_training = approved
        pothole.reviewed_by = reviewer  # property setter 사용
        pothole.reviewed_at = datetime.now()
        pothole.save()
        
        st.cache_data.clear()
        return True
    except Pothole.DoesNotExist:
        st.warning(f"포트홀 #{pothole_id}를 찾을 수 없습니다.")
        return False
    except Exception as e:
        st.error(f"업데이트 실패: {str(e)}")
        return False

def save_review_note(pothole_id, note):
    """검토 메모 저장 using Django ORM"""
    try:
        pothole = Pothole.objects.get(id=pothole_id)
        pothole.review_notes = note
        pothole.save()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"메모 저장 실패: {str(e)}")

# 메인 대시보드
def chatbot_sidebar():
    """사이드바에 표시되는 챗봇 UI"""
    st.header("💬 챗봇")
    st.markdown("자연어로 포트홀 데이터에 대해 질문하세요!")
    
    # NPU + Phi-3-mini만 사용
    # 연결 체크를 캐싱하여 반복 체크 방지
    if 'npu_connection_checked' not in st.session_state:
        st.session_state.npu_connection_checked = False
        st.session_state.npu_connection_result = False
    
    # 한 번만 체크하고 결과를 캐싱
    if not st.session_state.npu_connection_checked:
        if SLM_NPU_AVAILABLE:
            try:
                st.session_state.npu_connection_result = check_slm_npu_connection()
            except:
                st.session_state.npu_connection_result = True  # 실패해도 UI 표시
        else:
            st.session_state.npu_connection_result = False
        st.session_state.npu_connection_checked = True
    
    use_npu = SLM_NPU_AVAILABLE and st.session_state.npu_connection_result
    
    if use_npu:
        # 챗봇 초기화 (세션 상태에 저장)
        if 'road_chatbot' not in st.session_state:
            # OpenVINO NPU + Phi-3-mini 사용
            st.session_state.road_chatbot = SLMNPUChatbot()
            st.session_state.chatbot_type = "NPU"
        
        # 챗봇 타입 표시
        chatbot_type = st.session_state.get('chatbot_type', 'NPU')
        st.caption("🚀 **NPU 가속 활성화**: OpenVINO + Intel NPU + Phi-3-mini")
        
        # 채팅 히스토리 초기화
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # 채팅 히스토리 표시 (스크롤 가능) - 먼저 표시
        if st.session_state.chat_history:
            st.markdown("### 💬 대화 내역")
            
            # 최근 메시지부터 표시 (역순)
            for msg in reversed(st.session_state.chat_history[-10:]):  # 최근 10개만 표시
                if msg['role'] == 'user':
                    st.markdown(f"**👤 사용자:** {msg['content']}")
                    st.caption(f"*{msg['timestamp'].strftime('%H:%M:%S')}*")
                else:
                    st.markdown(f"**🤖 AI:** {msg['content']}")
                    st.caption(f"*{msg['timestamp'].strftime('%H:%M:%S')}*")
                
                st.markdown("---")
        
        # 대화 초기화 버튼
        if st.session_state.chat_history and st.button("🗑️ 대화 초기화", use_container_width=True, key="chatbot_clear_sidebar"):
            st.session_state.chat_history = []
            st.rerun()
        
        st.divider()
        
        # 처리 중이 아닐 때만 입력 받기
        processing = st.session_state.get('processing_question', False)
        
        # 처리 중 표시
        if processing:
            st.info("⏳ 답변 생성 중...")
        
        # 사용자 입력 (처리 중일 때는 비활성화)
        user_question = st.text_input(
            "질문 입력:",
            key="user_question_input_sidebar",
            value="",
            placeholder="예: 위험도가 높은 포트홀은?",
            disabled=processing,
            label_visibility="visible"
        )
        
        # 질문 버튼 (처리 중일 때는 비활성화)
        submit_button = st.button("📤 질문하기", type="primary", use_container_width=True, key="chatbot_submit_sidebar", disabled=processing)
        
        pending_question = st.session_state.get('pending_question', '')
        
        if submit_button and user_question and not processing:
            # 질문을 세션 상태에 저장하고 즉시 rerun
            st.session_state['pending_question'] = user_question
            st.rerun()
        
        # 대기 중인 질문 처리 (rerun 후)
        if pending_question and not processing:
            st.session_state['processing_question'] = True
            
            # 사용자 질문을 히스토리에 추가
            st.session_state.chat_history.append({
                'role': 'user',
                'content': pending_question,
                'timestamp': datetime.now()
            })
            
            # AI 답변 생성
            try:
                chatbot = st.session_state.road_chatbot
                response = chatbot.answer_question(pending_question)
                
                # AI 답변을 히스토리에 추가
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response['answer'],
                    'data': response.get('data'),
                    'image_path': response.get('image_path'),
                    'timestamp': datetime.now()
                })
            except Exception as e:
                st.error(f"답변 생성 중 오류 발생: {str(e)}")
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                    'timestamp': datetime.now()
                })
            finally:
                # 처리 완료 후 상태 초기화
                st.session_state['pending_question'] = ''
                st.session_state['processing_question'] = False
                st.rerun()
    else:
        st.error("⚠️ **NPU Worker가 연결되지 않았습니다.**")
        st.info("💡 NPU Worker를 시작한 후 페이지를 새로고침하세요.")


def main():
    # 사이드바
    with st.sidebar:
        st.header("필터")
        days = st.slider("최근 N일 데이터", 1, 30, 7)
        min_depth = st.slider("최소 깊이 비율", 0.0, 1.0, 0.1)
        
        st.header("우선순위 필터")
        min_priority = st.slider("최소 우선순위 점수", 0.0, 50.0, 0.0, 1.0)
        risk_level_filter = st.multiselect(
            "위험도 레벨",
            options=["critical", "high", "medium", "low"],
            default=["critical", "high", "medium", "low"]
        )
        location_type_filter = st.multiselect(
            "위치 유형",
            options=["highway", "school_zone", "school_area", "hospital_area", 
                    "bus_lane", "residential", "commercial", "general", "park"],
            default=[]  # 빈 배열이면 모든 유형 표시
        )
        
        st.header("새로고침")
        auto_refresh = st.checkbox("자동 새로고침 (5초)", value=False)
        if st.button("데이터 새로고침"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()
        
        if auto_refresh:
            st.info("자동 새로고침 활성화됨")
            time.sleep(5)
            st.cache_data.clear()
            st.rerun()
        
        st.header("데이터 내보내기")
        col1, col2 = st.columns([1, 1])
        with col1:
            export_format = st.radio("형식 선택", ["CSV", "JSON"], horizontal=True)
        with col2:
            if st.button("💬 챗봇", use_container_width=True, key="chatbot_toggle_sidebar"):
                if 'show_chatbot' not in st.session_state:
                    st.session_state.show_chatbot = True
                else:
                    st.session_state.show_chatbot = not st.session_state.show_chatbot
                st.rerun()
    
    # 오른쪽 사이드바 (챗봇)를 위한 레이아웃
    if st.session_state.get('show_chatbot', False):
        main_col, chatbot_col = st.columns([2.5, 1], gap="medium")
    else:
        main_col = st.container()
        chatbot_col = None
    
    # 오른쪽 사이드바에 챗봇 표시
    if chatbot_col:
        with chatbot_col:
            chatbot_sidebar()
    
    # 메인 컨텐츠는 main_col 안에 표시
    with main_col:
        st.title("🕳️ Deep-Guardian 포트홀 모니터링 대시보드")
        
        # 통계 카드
        stats = get_statistics()
        
        if stats is not None:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("전체 탐지 수", f"{int(stats['total_count']):,}")
            
            with col2:
                st.metric("검증 통과", f"{int(stats['validated_count']):,}")
            
            with col3:
                st.metric("평균 깊이 비율", f"{stats['avg_depth_ratio']:.3f}" if stats['avg_depth_ratio'] else "N/A")
            
            with col4:
                if stats['last_detection']:
                    last_dt = pd.to_datetime(stats['last_detection'])
                    st.metric("최근 탐지", last_dt.strftime("%Y-%m-%d %H:%M"))
        
        st.divider()
        
        # 데이터 로드
        df = get_potholes(limit=500)
        
        # filtered_df 초기화 (항상 정의되도록)
        filtered_df = pd.DataFrame()
        
        # 필터링 적용 (지도와 테이블 모두에 적용)
        if not df.empty:
            filtered_df = df[
                (df['depth_ratio'] >= min_depth) &
                (pd.to_datetime(df['detected_at']) >= datetime.now() - timedelta(days=days))
            ]
            
            # 우선순위 필터 적용
            if 'priority_score' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['priority_score'] >= min_priority]
            
            # 위험도 레벨 필터 적용
            if 'risk_level' in filtered_df.columns and risk_level_filter:
                filtered_df = filtered_df[filtered_df['risk_level'].isin(risk_level_filter)]
            
            # 위치 유형 필터 적용
            if 'location_type' in filtered_df.columns and location_type_filter:
                filtered_df = filtered_df[filtered_df['location_type'].isin(location_type_filter)]
            
            # 우선순위 점수로 정렬
            if 'priority_score' in filtered_df.columns:
                filtered_df = filtered_df.sort_values('priority_score', ascending=False)
        
        # 지도 시각화
        st.header("📍 포트홀 위치 지도")
        
        if not df.empty and not filtered_df.empty:
            # 지도 생성 (한국 중심)
            m = folium.Map(
                location=[37.5665, 126.9780],  # 서울 좌표
                zoom_start=10,
                tiles='OpenStreetMap'
            )
            
            # 필터링된 데이터로 포트홀 마커 추가
            for idx, row in filtered_df.iterrows():
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    # 우선순위에 따른 색상 결정
                    priority_score = row.get('priority_score', 1.0) if pd.notna(row.get('priority_score')) else 1.0
                    risk_level = row.get('risk_level', 'medium') if pd.notna(row.get('risk_level')) else 'medium'
                    
                    # 위험도에 따른 색상
                    if risk_level == 'critical' or priority_score >= 30:
                        color = 'darkred'
                        radius = 10
                    elif risk_level == 'high' or priority_score >= 20:
                        color = 'red'
                        radius = 8
                    elif risk_level == 'medium' or priority_score >= 10:
                        color = 'orange'
                        radius = 6
                    else:
                        color = 'yellow'
                        radius = 5
                    
                    # 검증 실패 시 회색
                    if not row['validation_result']:
                        color = 'gray'
                        radius = 4
                    
                    location_desc = row.get('location_description', '일반 도로') if pd.notna(row.get('location_description')) else '일반 도로'
                    
                    # 이미지 경로 확인 및 이미지 표시
                    image_path = row.get('image_path', '')
                    image_html = ""
                    if image_path and pd.notna(image_path):
                        # 공유 이미지 디렉토리 경로 처리
                        display_path = image_path.replace('/app/shared_images/', '/app/shared_images/')
                        
                        # 이미지 파일이 존재하면 base64로 인코딩하여 팝업에 표시
                        if os.path.exists(display_path):
                            try:
                                with open(display_path, 'rb') as img_file:
                                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                                    img_ext = os.path.splitext(display_path)[1].lower()
                                    mime_type = 'image/jpeg' if img_ext in ['.jpg', '.jpeg'] else 'image/png' if img_ext == '.png' else 'image/jpeg'
                                    image_html = f'<br><img src="data:{mime_type};base64,{img_data}" style="max-width:200px; max-height:150px; border:1px solid #ddd; border-radius:3px; margin-top:5px;" alt="포트홀 이미지"><br><small style="color: #666;">ID: {row["id"]}</small>'
                            except Exception as e:
                                image_html = f'<br><span style="color: orange;">⚠️ 이미지 로드 실패</span><br><small>ID: {row["id"]}</small>'
                        else:
                            # 이미지 파일이 없으면 안내 메시지
                            image_html = f'<br><span style="color: gray;">📷 이미지 파일 없음</span><br><small>ID: {row["id"]}</small>'
                    else:
                        image_html = '<br><span style="color: gray;">📷 이미지 정보 없음</span>'
                    
                    popup_text = f"""
                    <div style="font-size: 12px; max-width: 250px;">
                    <b>포트홀 #{row['id']}</b><br>
                    우선순위: {priority_score:.2f}<br>
                    위험도: {risk_level.upper()}<br>
                    위치: {location_desc}<br>
                    깊이 비율: {row['depth_ratio']:.3f}<br>
                    검증: {'통과' if row['validation_result'] else '실패'}<br>
                    탐지 시간: {row['detected_at']}<br>
                    {image_html}
                    </div>
                    """
                    folium.CircleMarker(
                        location=[row['latitude'], row['longitude']],
                        radius=radius,
                        popup=folium.Popup(popup_text, max_width=250),
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.7
                    ).add_to(m)
            
            # 지도 범례 추가 (오른쪽 상단, 작은 크기)
            legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 140px; height: auto; 
                    background-color: white; z-index:9999; font-size:11px;
                    border:2px solid grey; border-radius:5px; padding: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
        <h4 style="margin-top:0; margin-bottom:5px; font-size:12px; font-weight:bold;">위험도 범례</h4>
        <p style="margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; border-radius:50%; background-color:darkred; margin-right:5px;"></span> Critical</p>
        <p style="margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; border-radius:50%; background-color:red; margin-right:5px;"></span> High</p>
        <p style="margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; border-radius:50%; background-color:orange; margin-right:5px;"></span> Medium</p>
        <p style="margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; border-radius:50%; background-color:yellow; margin-right:5px;"></span> Low</p>
        <p style="margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; border-radius:50%; background-color:gray; margin-right:5px;"></span> 검증실패</p>
        <p style="margin-top:5px; margin-bottom:0; font-size:10px; font-weight:bold; border-top:1px solid #ddd; padding-top:3px;">표시: {count}개</p>
        </div>
            '''.format(count=len(filtered_df))
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # 지도 표시 (상호작용 시 자동 새로고침 방지)
            # returned_objects를 빈 리스트로 설정하여 모든 상호작용 무시
            map_data = st_folium(
                m, 
                width=1200, 
                height=600,
                returned_objects=[],  # 모든 이벤트 무시하여 rerun 방지
                key="pothole_map"  # 고유 키로 상태 유지
            )
            
            # 필터링된 데이터 개수 표시
            if len(filtered_df) < len(df):
                st.info(f"📍 지도에 표시된 포트홀: **{len(filtered_df)}개** (전체 {len(df)}개 중, 필터 적용됨)")
            else:
                st.info(f"📍 지도에 표시된 포트홀: **{len(filtered_df)}개**")
        elif not df.empty and filtered_df.empty:
            # 필터링 결과 데이터가 없는 경우
            st.warning("⚠️ 선택한 필터 조건에 맞는 포트홀이 없습니다. 필터 조건을 조정해주세요.")
            
            # 빈 지도 표시
            m = folium.Map(
                location=[37.5665, 126.9780],
                zoom_start=10,
                tiles='OpenStreetMap'
            )
            st_folium(m, width=1200, height=600, returned_objects=[], key="pothole_map_empty")
        else:
            # 데이터가 없는 경우
            st.info("아직 탐지된 포트홀이 없습니다. AI Core가 영상을 처리하면 데이터가 표시됩니다.")
        
        # 데이터 테이블 (지도와 독립적으로 항상 표시)
        st.header("📊 포트홀 데이터 테이블")
        
        # 데이터 내보내기 기능
        if not filtered_df.empty:
            st.subheader("📥 데이터 내보내기")
            col1, col2 = st.columns(2)
            
            with col1:
                if export_format == "CSV":
                    # CSV 내보내기
                    csv_buffer = io.StringIO()
                    # 필요한 컬럼만 선택
                    export_columns = ['id', 'priority_score', 'risk_level', 'location_type', 
                                     'location_description', 'latitude', 'longitude', 'depth_ratio', 
                                     'validation_result', 'detected_at']
                    export_columns = [col for col in export_columns if col in filtered_df.columns]
                    export_df = filtered_df[export_columns].copy()
                    export_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                    csv_data = csv_buffer.getvalue()
                    
                    st.download_button(
                        label="📄 CSV 다운로드",
                        data=csv_data,
                        file_name=f"potholes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help=f"Export {len(filtered_df)} records as CSV"
                    )
                else:
                    # JSON 내보내기
                    export_columns = ['id', 'priority_score', 'risk_level', 'location_type', 
                                     'location_description', 'latitude', 'longitude', 'depth_ratio', 
                                     'validation_result', 'detected_at']
                    export_columns = [col for col in export_columns if col in filtered_df.columns]
                    export_data = filtered_df[export_columns].to_dict('records')
                    json_data = json.dumps(export_data, indent=2, default=str, ensure_ascii=False)
                    
                    st.download_button(
                        label="📄 JSON 다운로드",
                        data=json_data,
                        file_name=f"potholes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                    help=f"Export {len(filtered_df)} records as JSON"
                )
            
            with col2:
                st.info(f"**내보낼 레코드 수:** {len(filtered_df)}개\n\n**필터 조건:**\n- 최근 {days}일\n- 최소 깊이: {min_depth}")
        
        # 이미지 뷰어 섹션
        if not filtered_df.empty:
            st.subheader("🖼️ 이미지 뷰어")
            selected_id = st.selectbox(
                "포트홀 ID 선택",
                options=filtered_df['id'].tolist(),
                format_func=lambda x: f"포트홀 #{x}"
            )
            
            if selected_id:
                selected_row = filtered_df[filtered_df['id'] == selected_id].iloc[0]
                image_path = selected_row.get('image_path')
                
                if image_path and pd.notna(image_path):
                    # 공유 이미지 디렉토리 경로 처리
                    if image_path.startswith('/app/shared_images/'):
                        # 공유 볼륨 경로 (대시보드에서 접근 가능)
                        display_path = image_path.replace('/app/shared_images/', '/app/shared_images/')
                        if os.path.exists(display_path):
                            try:
                                st.image(display_path, caption=f"Pothole #{selected_id}", use_container_width=True)
                            except Exception as e:
                                st.error(f"Failed to load image: {str(e)}")
                        else:
                            st.warning(f"Image file not found: {display_path}")
                    elif image_path.startswith('/app/temp/'):
                        # 임시 경로 (이전 데이터) - 이미지가 삭제되었을 수 있음
                        st.info("This image was from temporary processing. New detections will save images to shared directory.")
                        st.warning("Image file may have been deleted after processing.")
                    else:
                        # 다른 경로 시도
                        if os.path.exists(image_path):
                            try:
                                st.image(image_path, caption=f"Pothole #{selected_id}", use_container_width=True)
                            except Exception as e:
                                st.error(f"Failed to load image: {str(e)}")
                        else:
                            st.warning(f"Image file not found: {image_path}")
                else:
                    st.info("No image path information available for this pothole.")
                
                # 선택된 포트홀 정보 표시
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("우선순위", f"{selected_row.get('priority_score', 0):.2f}" if pd.notna(selected_row.get('priority_score')) else "N/A")
                with col2:
                    risk_level = selected_row.get('risk_level', 'medium') if pd.notna(selected_row.get('risk_level')) else 'medium'
                    st.metric("위험도", risk_level.upper())
                with col3:
                    st.metric("깊이 비율", f"{selected_row['depth_ratio']:.3f}")
                with col4:
                    st.metric("검증 결과", "통과" if selected_row['validation_result'] else "실패")
                
                # 위치 정보 표시
                if pd.notna(selected_row.get('location_description')):
                    st.info(f"📍 위치: {selected_row.get('location_description')}")
                
                # 추가 정보
                st.metric("탐지 시간", pd.to_datetime(selected_row['detected_at']).strftime("%Y-%m-%d %H:%M"))
        
        # 데이터 테이블 표시 (지도와 독립적으로 항상 표시)
        if not filtered_df.empty:
            # 데이터 테이블 표시
            display_df = filtered_df.copy()
            
            # 컬럼 선택 및 변환
            display_columns = ['id', 'priority_score', 'risk_level', 'location_description', 
                              'latitude', 'longitude', 'depth_ratio', 'validation_result', 'detected_at']
            
            # 존재하는 컬럼만 선택
            available_columns = [col for col in display_columns if col in display_df.columns]
            display_df = display_df[available_columns].copy()
            
            # validation_result를 텍스트로 변환
            if 'validation_result' in display_df.columns:
                display_df['Validation'] = display_df['validation_result'].apply(lambda x: "Pass" if x else "Fail")
                display_df = display_df.drop(columns=['validation_result'])
            
            # 컬럼명 한글화
            column_mapping = {
                'id': 'ID',
                'priority_score': '우선순위',
                'risk_level': '위험도',
                'location_description': '위치',
                'latitude': '위도',
                'longitude': '경도',
                'depth_ratio': '깊이 비율',
                'detected_at': '탐지 시간'
            }
            display_df = display_df.rename(columns=column_mapping)
            
            # 우선순위 점수 포맷팅
            if '우선순위' in display_df.columns:
                display_df['우선순위'] = display_df['우선순위'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
            
            # 위험도 한글화
            if '위험도' in display_df.columns:
                risk_mapping = {
                    'critical': '긴급',
                    'high': '높음',
                    'medium': '보통',
                    'low': '낮음'
                }
                display_df['위험도'] = display_df['위험도'].apply(lambda x: risk_mapping.get(x, x) if pd.notna(x) else 'N/A')
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # 차트
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("깊이 비율 분포")
                if 'depth_ratio' in filtered_df.columns:
                    try:
                        fig = px.histogram(
                            filtered_df, 
                            x='depth_ratio',
                            nbins=20,
                            title="깊이 비율 히스토그램",
                            labels={'depth_ratio': '깊이 비율', 'count': '개수'}
                        )
                        # 히스토그램 막대 간격 조정
                        fig.update_traces(
                            marker_line_width=0.5,
                            marker_line_color='white'
                        )
                        fig.update_layout(
                            bargap=0.1,  # 막대 간격 조정
                            bargroupgap=0.05  # 그룹 간 간격
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"차트 생성 중 오류 발생: {str(e)}")
                else:
                    st.info("깊이 비율 데이터가 없습니다.")
            
            with col2:
                st.subheader("일별 탐지 수")
                if 'detected_at' in filtered_df.columns and not filtered_df['detected_at'].isna().all():
                    try:
                        # 일별 탐지 수 계산
                        filtered_df_copy = filtered_df.copy()
                        # datetime으로 변환하고 날짜만 추출
                        filtered_df_copy['date'] = pd.to_datetime(filtered_df_copy['detected_at'], errors='coerce').dt.date
                        # None 값 제거
                        filtered_df_copy = filtered_df_copy[filtered_df_copy['date'].notna()]
                        
                        if not filtered_df_copy.empty:
                            daily_counts = filtered_df_copy['date'].value_counts().sort_index()
                            
                            # DataFrame으로 변환 (날짜를 문자열로 변환)
                            daily_df = pd.DataFrame({
                                'date': [str(d) for d in daily_counts.index],
                                'count': daily_counts.values
                            })
                            
                            if not daily_df.empty and len(daily_df) > 0:
                                # 막대 차트 생성
                                fig = go.Figure()
                                
                                fig.add_trace(go.Bar(
                                    x=daily_df['date'],
                                    y=daily_df['count'],
                                    text=daily_df['count'],
                                    textposition='outside',
                                    marker=dict(
                                        color='steelblue',
                                        line=dict(color='white', width=0.5)
                                    ),
                                    hovertemplate='<b>날짜:</b> %{x}<br><b>탐지 수:</b> %{y}<extra></extra>'
                                ))
                                
                                # 레이아웃 설정
                                fig.update_layout(
                                    title="일별 포트홀 탐지 수",
                                    xaxis=dict(
                                        title='날짜',
                                        tickangle=-45,
                                        showgrid=True,
                                        gridwidth=1,
                                        gridcolor='lightgray'
                                    ),
                                    yaxis=dict(
                                        title='탐지 수',
                                        showgrid=True,
                                        gridwidth=1,
                                        gridcolor='lightgray'
                                    ),
                                    bargap=0.2,
                                    height=400,
                                    hovermode='x unified',
                                    showlegend=False
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("일별 탐지 데이터가 없습니다.")
                        else:
                            st.info("유효한 탐지 날짜 데이터가 없습니다.")
                    except Exception as e:
                        st.warning(f"차트 생성 중 오류 발생: {str(e)}")
                        import traceback
                        with st.expander("오류 상세 정보"):
                            st.code(traceback.format_exc())
                else:
                    st.info("탐지 날짜 데이터가 없습니다.")
        elif not df.empty:
            st.info("⚠️ 선택한 필터 조건에 맞는 포트홀이 없습니다. 필터 조건을 조정해주세요.")
        else:
            st.info("아직 탐지된 포트홀이 없습니다. AI Core가 영상을 처리하면 데이터가 표시됩니다.")

# 페이지 라우팅
def app():
    """메인 앱 - 인증 및 페이지 라우팅"""
    # 기본 사용자 계정 생성 (최초 실행 시)
    try:
        from create_default_users import create_default_users
        create_default_users()
    except Exception as e:
        pass  # 이미 생성되었거나 오류 발생 시 무시
    
    # 세션 상태 초기화
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    
    # 로그인 상태 확인
    is_logged_in = check_authentication()
    
    # 로그인 페이지 표시 (관리자 로그인 버튼 클릭 시)
    if st.session_state.show_login and not is_logged_in:
        login_page()
        # 로그인 성공 시
        if check_authentication():
            st.session_state.show_login = False
            st.rerun()
        return
    
    # 사이드바에 로그인/로그아웃 및 메뉴
    with st.sidebar:
        if is_logged_in:
            # 로그인된 경우
            st.write("---")
            user = st.session_state.user
            st.write(f"**로그인**: {user['username']}")
            st.write(f"**역할**: {'관리자' if user['role'] == 'admin' else '일반 사용자'}")
            if st.button("로그아웃", use_container_width=True):
                logout()
        else:
            # 로그인되지 않은 경우
            st.write("---")
            st.write("**게스트 모드**")
            st.info("일반 사용자는 로그인 없이 이용 가능합니다.")
            if st.button("관리자 로그인", use_container_width=True):
                st.session_state.show_login = True
                st.rerun()
        
        st.write("---")
        
        # 페이지 선택
        if is_logged_in and is_admin():
            # 관리자 로그인 시
            st.header("관리자 메뉴")
            page = st.radio(
                "페이지 선택",
                ["대시보드", "이미지 검토", "비디오 추론 결과"],
                key="page_selector"
            )
        else:
            # 일반 사용자 또는 비로그인 사용자
            st.header("메뉴")
            
            if 'page_selector_user' not in st.session_state:
                st.session_state.page_selector_user = "대시보드"
            
            # 일반 사용자는 대시보드만 접근 가능
            page_options = ["대시보드"]
            
            # 위젯 생성 전에 현재 선택된 페이지를 확인
            selected_page = st.radio(
                "페이지 선택",
                page_options,
                key="page_selector_user",
                index=0
            )
            page = selected_page
    
    # 페이지 라우팅
    if page == "대시보드":
        main()
    elif page == "이미지 검토":
        # 관리자만 접근 가능
        if is_logged_in and is_admin():
            admin_review_page()
        else:
            st.error("⚠️ 이미지 검토 기능은 관리자만 접근할 수 있습니다.")
            st.info("관리자로 로그인해주세요.")
            if st.button("관리자 로그인", key="admin_login_from_error"):
                st.session_state.show_login = True
                st.rerun()
    elif page == "비디오 추론 결과":
        # 관리자만 접근 가능
        if is_logged_in and is_admin():
            video_results_page()
        else:
            st.error("⚠️ 비디오 추론 결과 기능은 관리자만 접근할 수 있습니다.")
            st.info("관리자로 로그인해주세요.")
            if st.button("관리자 로그인", key="admin_login_from_video_error"):
                st.session_state.show_login = True
                st.rerun()
    else:
        main()  # 기본적으로 대시보드 표시

if __name__ == "__main__":
    app()


