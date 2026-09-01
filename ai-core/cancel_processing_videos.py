#!/usr/bin/env python3
"""
처리 중인 비디오 취소 스크립트
AI Core 컨테이너 내부에서 실행
"""

import os
import shutil
import sys
import json

def cancel_processing_videos():
    """처리 중인 비디오 결과 디렉토리 삭제 및 재처리 가능하도록 설정"""
    video_results_dir = "/app/shared_images/video_results"
    processed_videos_file = "/app/processed_videos.json"
    videos_dir = "/app/videos"
    
    cancelled_items = []
    errors = []
    removed_from_processed = []
    
    # 비디오 결과 디렉토리에서 처리 중인 항목 찾기 및 삭제
    if os.path.exists(video_results_dir):
        try:
            items = os.listdir(video_results_dir)
            for item in items:
                item_path = os.path.join(video_results_dir, item)
                if os.path.isdir(item_path):
                    info_file = os.path.join(item_path, "video_info.json")
                    if os.path.exists(info_file):
                        try:
                            # 파일이 큰 경우를 대비해 첫 부분만 읽기
                            with open(info_file, 'r', encoding='utf-8') as f:
                                content = f.read(5000)  # 처음 5KB만 읽기
                                if '"status": "processing"' in content:
                                    # 처리 중인 비디오 발견
                                    try:
                                        # video_info.json에서 원본 비디오 경로 확인
                                        f.seek(0)
                                        video_info = json.load(f)
                                        video_name = video_info.get('video_name', '')
                                        video_path = video_info.get('video_path', '')
                                        
                                        # 결과 디렉토리 삭제
                                        shutil.rmtree(item_path)
                                        cancelled_items.append({
                                            'directory': item,
                                            'video_name': video_name,
                                            'video_path': video_path
                                        })
                                        
                                        # processed_videos.json에서 제거하여 재처리 가능하도록
                                        if os.path.exists(processed_videos_file):
                                            try:
                                                with open(processed_videos_file, 'r', encoding='utf-8') as pf:
                                                    processed = json.load(pf)
                                                
                                                # 원본 비디오 경로로 찾아서 제거
                                                if video_path and video_path in processed:
                                                    del processed[video_path]
                                                    removed_from_processed.append(video_path)
                                                
                                                # /app/videos/ 경로로도 확인
                                                if video_name:
                                                    videos_path = os.path.join(videos_dir, video_name)
                                                    if videos_path in processed:
                                                        del processed[videos_path]
                                                        removed_from_processed.append(videos_path)
                                                
                                                # 변경사항 저장
                                                if removed_from_processed:
                                                    with open(processed_videos_file, 'w', encoding='utf-8') as pf:
                                                        json.dump(processed, pf, indent=2, ensure_ascii=False)
                                            except Exception as e:
                                                errors.append(f"processed_videos.json 업데이트 실패: {str(e)}")
                                        
                                    except Exception as e:
                                        errors.append(f"{item} 삭제 실패: {str(e)}")
                        except Exception as e:
                            errors.append(f"{item} 정보 읽기 실패: {str(e)}")
        except Exception as e:
            errors.append(f"디렉토리 읽기 실패: {str(e)}")
    
    # 결과 출력
    result = {
        "success": len(errors) == 0,
        "cancelled_count": len(cancelled_items),
        "cancelled_items": cancelled_items,
        "removed_from_processed": removed_from_processed,
        "errors": errors
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    try:
        result = cancel_processing_videos()
        sys.exit(0 if result["success"] else 1)
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)

