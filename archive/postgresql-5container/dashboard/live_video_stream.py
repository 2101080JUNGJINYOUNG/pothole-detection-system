"""
실시간 비디오 추론 스트리밍 페이지
동영상 처리 중 실시간으로 프레임별 추론 결과를 확인
"""

import streamlit as st
import os
import json
import time
from datetime import datetime
import cv2
from PIL import Image

def live_video_stream_page():
    """실시간 비디오 추론 스트리밍 페이지"""
    st.title("🎥 실시간 비디오 추론 스트리밍")
    
    # 실시간 스트리밍 디렉토리
    streaming_dir = "/app/shared_images/video_streaming"
    current_video_stream_file = os.path.join(streaming_dir, "current_video.json")
    current_frame_path = os.path.join(streaming_dir, "current_frame.jpg")
    
    # 자동 새로고침 설정
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        auto_refresh = st.checkbox("자동 새로고침", value=True, key="auto_refresh")
    with col2:
        refresh_interval = st.selectbox("새로고침 간격 (초)", [0.5, 1, 2, 5], index=1, key="refresh_interval")
    with col3:
        if st.button("🔄 수동 새로고침", use_container_width=True, key="manual_refresh"):
            st.rerun()
    
    # 자동 새로고침을 위한 placeholder
    placeholder = st.empty()
    
    # 실시간 스트리밍 정보 읽기
    if not os.path.exists(current_video_stream_file):
        st.info("현재 처리 중인 비디오가 없습니다. 비디오를 `/app/videos` 디렉토리에 넣으면 실시간 추론 과정을 확인할 수 있습니다.")
        return
    
    try:
        with open(current_video_stream_file, 'r', encoding='utf-8') as f:
            streaming_info = json.load(f)
    except Exception as e:
        st.error(f"스트리밍 정보를 읽을 수 없습니다: {str(e)}")
        return
    
    # 비디오 정보 표시
    status = streaming_info.get("status", "unknown")
    status_color = {
        "processing": "🟢",
        "completed": "✅",
        "unknown": "⚪"
    }
    status_text = {
        "processing": "처리 중",
        "completed": "처리 완료",
        "unknown": "알 수 없음"
    }
    
    st.markdown("---")
    
    # 상태 및 비디오 정보
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("상태", f"{status_color.get(status, '⚪')} {status_text.get(status, '알 수 없음')}")
    with col2:
        if status == "completed":
            # 완료된 경우 처리된 프레임 수 표시
            st.metric("처리된 프레임", f"{streaming_info.get('processed_frames', 0):,} / {streaming_info.get('total_frames', 0):,}")
        else:
            st.metric("현재 프레임", f"{streaming_info.get('current_frame', 0):,} / {streaming_info.get('total_frames', 0):,}")
    with col3:
        if status == "completed":
            st.metric("진행률", "100.0%")
        else:
            progress = (streaming_info.get('current_frame', 0) / streaming_info.get('total_frames', 1) * 100) if streaming_info.get('total_frames', 0) > 0 else 0
            st.metric("진행률", f"{progress:.1f}%")
    with col4:
        st.metric("총 탐지 수", f"{streaming_info.get('total_detections', 0)}")
    
    st.write(f"**비디오 파일**: {streaming_info.get('video_name', 'Unknown')}")
    st.write(f"**FPS**: {streaming_info.get('fps', 0):.2f}")
    st.write(f"**처리 시작 시간**: {streaming_info.get('start_time', 'Unknown')}")
    if status == "completed" and "end_time" in streaming_info:
        st.write(f"**처리 완료 시간**: {streaming_info.get('end_time', 'Unknown')}")
    
    st.markdown("---")
    
    # 진행률 바
    if streaming_info.get('total_frames', 0) > 0:
        if status == "completed":
            st.progress(1.0, text=f"처리 완료: {streaming_info.get('processed_frames', 0)} / {streaming_info.get('total_frames', 0)} 프레임")
        else:
            progress_value = streaming_info.get('current_frame', 0) / streaming_info.get('total_frames', 1)
            st.progress(progress_value, text=f"프레임 {streaming_info.get('current_frame', 0)} / {streaming_info.get('total_frames', 0)} 처리 중...")
    
    st.markdown("---")
    
    # 실시간 프레임 표시
    st.subheader("실시간 추론 프레임")
    
    if os.path.exists(current_frame_path):
        try:
            # 이미지 표시
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.image(current_frame_path, caption="현재 처리 중인 프레임", use_container_width=True)
            
            with col2:
                frame_info = streaming_info.get("latest_frame_info", {})
                if frame_info:
                    st.write("**프레임 정보**")
                    st.write(f"**프레임 번호**: {frame_info.get('frame_number', 'N/A')}")
                    st.write(f"**시간**: {frame_info.get('timestamp', 0):.2f}초")
                    st.write(f"**탐지 수**: {len(frame_info.get('detections', []))}")
                    st.write(f"**진행률**: {frame_info.get('progress', 0):.1f}%")
                    
                    detections = frame_info.get('detections', [])
                    if detections:
                        st.write("**탐지된 포트홀:**")
                        for i, det in enumerate(detections, 1):
                            bbox = det.get('bbox', [])
                            conf = det.get('confidence', 0)
                            st.write(f"{i}. 신뢰도: {conf:.3f}")
                            if len(bbox) == 4:
                                st.write(f"   위치: ({bbox[0]}, {bbox[1]}) - ({bbox[2]}, {bbox[3]})")
                    else:
                        st.info("포트홀 미탐지")
                else:
                    st.info("프레임 정보 없음")
        except Exception as e:
            st.error(f"이미지를 표시할 수 없습니다: {str(e)}")
    else:
        st.warning("현재 프레임 이미지를 찾을 수 없습니다.")
    
    # 자동 새로고침 (처리 중일 때만)
    if auto_refresh and status == "processing":
        with placeholder:
            st.info(f"⏳ {refresh_interval}초 후 자동 새로고침...")
        time.sleep(refresh_interval)
        st.rerun()
    
    # 처리 완료 시 메시지
    if status == "completed":
        video_creating = streaming_info.get("video_creating", False)
        if video_creating:
            st.info("⏳ 비디오 처리는 완료되었습니다. 동영상 생성 중... 잠시만 기다려주세요.")
        else:
            st.success("✅ 비디오 처리가 완료되었습니다! '비디오 추론 결과' 페이지에서 전체 결과를 확인할 수 있습니다.")
            if st.button("비디오 추론 결과 페이지로 이동", key="go_to_results"):
                # 위젯이 이미 생성된 경우, 임시 키를 사용하여 페이지 전환
                st.session_state._redirect_to_results = True
                st.rerun()
        
        # 동영상 생성 중이면 자동 새로고침
        if video_creating and auto_refresh:
            time.sleep(2)  # 2초마다 확인
            st.rerun()

