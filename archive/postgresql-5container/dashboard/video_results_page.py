"""
비디오 추론 결과 페이지
프레임별 추론 결과를 시각화하여 확인
관리자 전용 페이지
"""

import streamlit as st
import os
import json
import cv2
from PIL import Image
import pandas as pd
import shutil
import time
from auth import check_authentication, is_admin

def video_results_page():
    """비디오 추론 결과 확인 페이지 (관리자 전용)"""
    # 관리자 권한 확인
    if not check_authentication():
        st.error("⚠️ 로그인이 필요합니다.")
        st.info("관리자로 로그인해주세요.")
        if st.button("관리자 로그인", key="admin_login_from_video_page"):
            st.session_state.show_login = True
            st.rerun()
        return
    
    if not is_admin():
        st.error("⚠️ 이 페이지는 관리자만 접근할 수 있습니다.")
        st.info("관리자 계정으로 로그인해주세요.")
        if st.button("관리자 로그인", key="admin_login_from_video_page_2"):
            st.session_state.show_login = True
            st.rerun()
        return
    
    st.title("🎬 비디오 추론 결과")
    
    # 비디오 결과 디렉토리
    video_results_dir = "/app/shared_images/video_results"
    processed_videos_file = "/app/processed_videos.json"
    
    # 삭제 기능 추가
    if os.path.exists(video_results_dir) and len(os.listdir(video_results_dir)) > 0:
        st.sidebar.divider()
        st.sidebar.subheader("⚙️ 관리")
        
        if st.sidebar.button("🗑️ 모든 비디오 결과 삭제", type="primary", use_container_width=True):
            try:
                # 비디오 결과 디렉토리 삭제
                if os.path.exists(video_results_dir):
                    for item in os.listdir(video_results_dir):
                        item_path = os.path.join(video_results_dir, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                    st.sidebar.success("✅ 모든 비디오 결과가 삭제되었습니다.")
                
                # 처리된 비디오 목록도 삭제
                if os.path.exists(processed_videos_file):
                    os.remove(processed_videos_file)
                    st.sidebar.success("✅ 처리된 비디오 목록이 초기화되었습니다.")
                
                st.sidebar.info("🔄 페이지를 새로고침하면 변경사항이 반영됩니다.")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"❌ 삭제 중 오류 발생: {str(e)}")
    
    if not os.path.exists(video_results_dir):
        st.info("아직 처리된 비디오가 없습니다. 비디오를 처리하면 결과가 여기에 표시됩니다.")
        st.info("💡 새 비디오를 추론하려면 `/app/videos` 디렉토리에 비디오 파일을 넣어주세요.")
        return
    
    # 처리 중인 비디오와 완료된 비디오 목록 가져오기
    processing_videos = []
    completed_videos = []
    
    try:
        items = os.listdir(video_results_dir)
    except Exception:
        items = []
    
    for item in items:
        item_path = os.path.join(video_results_dir, item)
        if os.path.isdir(item_path):
            info_file = os.path.join(item_path, "video_info.json")
            if os.path.exists(info_file):
                try:
                    # 파일이 큰 경우를 대비해 필요한 필드만 읽기
                    with open(info_file, 'r', encoding='utf-8') as f:
                        # 파일 크기 확인 (10MB 이상이면 frames 필드 제외하고 읽기)
                        file_size = os.path.getsize(info_file)
                        if file_size > 10 * 1024 * 1024:  # 10MB
                            # 큰 파일의 경우 스트리밍 방식으로 읽기
                            content = f.read()
                            # frames 필드가 있으면 제거 (메모리 절약)
                            video_info = json.loads(content)
                            if 'frames' in video_info:
                                # frames는 메모리에 저장하지 않음 (이미 처리됨)
                                video_info['frames'] = []
                        else:
                            video_info = json.load(f)
                        
                        video_info['directory'] = item
                        # status 필드가 없으면 파일 존재 여부로 판단
                        status = video_info.get('status', 'unknown')
                        if status == 'unknown':
                            # status가 없으면 completed로 간주 (기존 파일)
                            status = 'completed'
                            video_info['status'] = 'completed'
                        
                        if status == 'processing':
                            processing_videos.append(video_info)
                        elif status == 'completed':
                            completed_videos.append(video_info)
                        else:
                            # unknown 상태도 completed로 처리
                            completed_videos.append(video_info)
                except json.JSONDecodeError as e:
                    st.warning(f"비디오 정보 JSON 파싱 실패: {item} - {str(e)}")
                except Exception as e:
                    st.warning(f"비디오 정보 로드 실패: {item} - {str(e)}")
    
    # 처리 중인 비디오와 완료된 비디오 합치기 (처리 중인 비디오를 먼저 표시)
    video_dirs = processing_videos + completed_videos
    
    if not video_dirs:
        st.info("처리된 비디오가 없습니다.")
        st.info("💡 새 비디오를 추론하려면 `/app/videos` 디렉토리에 비디오 파일을 넣어주세요.")
        return
    
    st.divider()
    
    # 비디오 선택 (처리 중인 비디오와 완료된 비디오)
    # 상태 표시를 위해 비디오 이름에 상태 추가
    video_options = {}
    for v in sorted(video_dirs, key=lambda x: (
        0 if x.get('status') == 'processing' else 1,  # 처리 중인 비디오를 먼저
        x['start_time']
    ), reverse=True):
        status_label = "🟢 처리 중" if v.get('status') == 'processing' else "✅ 완료"
        video_key = f"{status_label} - {v['video_name']} ({v['start_time'][:19]})"
        video_options[video_key] = v
    
    selected_video_name = st.selectbox(
        "비디오 선택",
        options=list(video_options.keys()),
        key="video_selector"
    )
    
    if selected_video_name:
        video_info = video_options[selected_video_name]
        
        # 비디오 정보 표시
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 프레임", f"{video_info['total_frames']:,}")
        with col2:
            st.metric("처리된 프레임", f"{video_info['processed_frames']}")
        with col3:
            st.metric("총 탐지 수", f"{video_info['total_detections']}")
        with col4:
            st.metric("FPS", f"{video_info['fps']:.2f}")
        
        st.write(f"**비디오 파일**: {video_info['video_name']}")
        st.write(f"**처리 시작**: {video_info['start_time']}")
        if video_info.get('status') == 'completed' and 'end_time' in video_info:
            st.write(f"**처리 완료**: {video_info['end_time']}")
        else:
            st.write(f"**상태**: 🟢 처리 중...")
        st.write(f"**프레임 간격**: {video_info['frame_interval']} 프레임마다 처리")
        
        # 처리 중인 경우 진행률 표시
        if video_info.get('status') == 'processing':
            total_frames = video_info.get('total_frames', 0)
            processed_frames = video_info.get('processed_frames', 0)
            if total_frames > 0:
                progress = processed_frames / total_frames
                st.progress(progress, text=f"처리 중: {processed_frames} / {total_frames} 프레임 ({progress*100:.1f}%)")
        
        st.divider()
        
        # 처리 중인 경우 진행 상태 표시
        if video_info.get('status') == 'processing':
            st.info("⏳ 비디오 처리가 진행 중입니다. 완료되면 동영상이 표시됩니다.")
            st.write("**참고**: 처리 완료 후 페이지를 새로고침하면 동영상을 확인할 수 있습니다.")
            
            # 자동 새로고침 옵션
            auto_refresh = st.checkbox("자동 새로고침", value=True, key="auto_refresh_video")
            if auto_refresh:
                import time
                time.sleep(2)  # 2초마다 새로고침
                st.rerun()
            
            # 처리 중일 때는 동영상 표시하지 않음
            return
        
        # 추론 결과 동영상 표시 및 다운로드
        result_video_path = None
        
        # result_video_path가 video_info에 있는 경우
        if 'result_video_path' in video_info and video_info['result_video_path']:
            result_video_path = video_info['result_video_path']
            # 경로 정규화
            if not result_video_path.startswith('/app'):
                result_video_path = os.path.join("/app/shared_images/video_results", video_info['directory'], 
                                                os.path.basename(result_video_path))
            result_video_path = os.path.normpath(result_video_path)
        
        # result_video_path가 없거나 파일이 없는 경우, 자동으로 찾기
        if not result_video_path or not os.path.exists(result_video_path):
            # 동영상 파일 자동 검색
            result_dir = os.path.join("/app/shared_images/video_results", video_info['directory'])
            video_basename = os.path.splitext(video_info.get('video_name', ''))[0]
            if video_basename:
                possible_video_path = os.path.join(result_dir, f"{video_basename}_result.mp4")
                if os.path.exists(possible_video_path):
                    result_video_path = possible_video_path
                    # video_info에 저장 (다음에 빠르게 찾을 수 있도록)
                    if 'result_video_path' not in video_info:
                        video_info['result_video_path'] = result_video_path
                        # video_info.json 업데이트
                        try:
                            info_file = os.path.join(result_dir, "video_info.json")
                            with open(info_file, 'w', encoding='utf-8') as f:
                                json.dump(video_info, f, indent=2, ensure_ascii=False)
                        except Exception as e:
                            pass  # 업데이트 실패해도 계속 진행
        
        if result_video_path and os.path.exists(result_video_path):
            st.subheader("📹 추론 결과 동영상")
            try:
                # 동영상 파일 읽기
                with open(result_video_path, 'rb') as video_file:
                    video_bytes = video_file.read()
                    video_name = os.path.basename(result_video_path)
                    file_size = len(video_bytes)
                    
                    st.write(f"**파일 크기**: {file_size / (1024*1024):.2f} MB")
                    
                    # 다운로드 버튼만 표시
                    st.download_button(
                        label="📥 추론 결과 동영상 다운로드",
                        data=video_bytes,
                        file_name=video_name,
                        mime="video/mp4",
                        key=f"download_{video_info['directory']}"
                    )
            except Exception as e:
                st.error(f"동영상 파일을 읽을 수 없습니다: {str(e)}")
                st.write(f"동영상 경로: {result_video_path}")
                import traceback
                st.code(traceback.format_exc())
        elif video_info.get('status') == 'completed':
            # 완료되었지만 동영상이 없는 경우
            st.info("⏳ 동영상 생성 중이거나 아직 생성되지 않았습니다. 잠시 후 다시 확인해주세요.")
            # 디버깅 정보
            result_dir = os.path.join("/app/shared_images/video_results", video_info['directory'])
            if os.path.exists(result_dir):
                files = os.listdir(result_dir)
                st.write(f"디렉토리 내 파일: {', '.join(files[:10])}")
        

