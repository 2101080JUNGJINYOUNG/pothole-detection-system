#!/usr/bin/env python3
"""
비디오 추론 결과 삭제 스크립트
AI Core 컨테이너 내부에서 실행
"""

import os
import shutil
import sys
import json

def delete_video_results():
    """비디오 추론 결과 디렉토리 삭제"""
    video_results_dir = "/app/shared_images/video_results"
    processed_videos_file = "/app/processed_videos.json"
    
    deleted_items = []
    errors = []
    
    # 비디오 결과 디렉토리 삭제
    if os.path.exists(video_results_dir):
        try:
            items = os.listdir(video_results_dir)
            for item in items:
                item_path = os.path.join(video_results_dir, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        deleted_items.append(f"디렉토리: {item}")
                    else:
                        os.remove(item_path)
                        deleted_items.append(f"파일: {item}")
                except Exception as e:
                    errors.append(f"{item}: {str(e)}")
        except Exception as e:
            errors.append(f"디렉토리 읽기 실패: {str(e)}")
    
    # 처리된 비디오 목록 파일 삭제
    if os.path.exists(processed_videos_file):
        try:
            os.remove(processed_videos_file)
            deleted_items.append(f"파일: processed_videos.json")
        except Exception as e:
            errors.append(f"processed_videos.json 삭제 실패: {str(e)}")
    
    # 결과 출력
    result = {
        "success": len(errors) == 0,
        "deleted_count": len(deleted_items),
        "deleted_items": deleted_items,
        "errors": errors
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    try:
        result = delete_video_results()
        sys.exit(0 if result["success"] else 1)
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        sys.exit(1)

