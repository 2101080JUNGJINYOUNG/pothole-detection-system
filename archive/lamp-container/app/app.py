"""
Deep-Guardian LAMP Container Web Application
Flask 기반 웹 애플리케이션
"""

from flask import Flask, render_template, jsonify, request, send_from_directory, session, make_response
from flask_cors import CORS
import os
import sys
import json
import csv
import io
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg, Max

# Django ORM 설정
sys.path.insert(0, '/var/www/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')

try:
    import django
    django.setup()
    from django_app.models import Pothole, User
    from django.db import connection
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Django not available: {e}")
    DJANGO_AVAILABLE = False

# Phi-3 챗봇 import
try:
    from phi3_chatbot import get_chatbot
    PHI3_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Phi-3 chatbot not available: {e}")
    PHI3_AVAILABLE = False

# 고급 챗봇 import
try:
    from advanced_chatbot import get_advanced_chatbot
    ADVANCED_CHATBOT_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Advanced chatbot not available: {e}")
    ADVANCED_CHATBOT_AVAILABLE = False

# 통계 모듈 import
try:
    from statistics import get_statistics
    STATISTICS_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Statistics module not available: {e}")
    STATISTICS_AVAILABLE = False

# 인증 모듈 import
try:
    from auth import authenticate_user, check_authentication, is_admin, login_required, admin_required, get_current_user
    AUTH_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Auth module not available: {e}")
    AUTH_AVAILABLE = False

app = Flask(__name__, 
            template_folder='/var/www/html',
            static_folder='/var/www/html')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'deep-guardian-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# 데이터베이스 연결 확인
def check_db_connection():
    """데이터베이스 연결 확인"""
    try:
        if DJANGO_AVAILABLE:
            from django.db import connection
            connection.ensure_connection()
            return True
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
    return False

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('dashboard.html')

@app.route('/health')
def health():
    """헬스 체크"""
    db_status = check_db_connection()
    phi3_status = False
    if PHI3_AVAILABLE:
        try:
            chatbot = get_chatbot()
            phi3_status = chatbot.is_model_loaded() if chatbot else False
        except:
            pass
    
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if db_status else 'disconnected',
        'phi3_chatbot': 'loaded' if phi3_status else 'not_loaded'
    })

@app.route('/api/potholes')
def get_potholes():
    """포트홀 데이터 조회 API (필터링 및 정렬 지원)"""
    try:
        if not DJANGO_AVAILABLE:
            return jsonify({'error': 'Django not available'}), 500
        
        # 쿼리 파라미터
        limit = request.args.get('limit', 100, type=int)
        validated_only = request.args.get('validated', 'false').lower() == 'true'
        days = request.args.get('days', 0, type=int)
        min_depth = request.args.get('min_depth', 0.0, type=float)
        min_priority = request.args.get('min_priority', 0.0, type=float)
        risk_levels = request.args.getlist('risk_level')
        location_types = request.args.getlist('location_type')
        sort_by = request.args.get('sort_by', 'detected_at')
        sort_order = request.args.get('sort_order', 'desc')
        review_status = request.args.get('review_status', None)  # 'pending', 'approved', 'rejected'
        
        # 데이터 조회
        query = Pothole.objects.all()
        
        # 날짜 필터
        if days > 0:
            start_date = datetime.now().date() - timedelta(days=days)
            query = query.filter(detected_at__date__gte=start_date)
        
        # 검증 필터
        if validated_only:
            query = query.filter(validation_result=True)
        
        # 깊이 필터
        if min_depth > 0:
            query = query.filter(depth_ratio__gte=min_depth)
        
        # 우선순위 필터
        if min_priority > 0:
            query = query.filter(priority_score__gte=min_priority)
        
        # 위험도 필터
        if risk_levels:
            query = query.filter(risk_level__in=risk_levels)
        
        # 위치 유형 필터
        if location_types:
            query = query.filter(location_type__in=location_types)
        
        # 검토 상태 필터
        if review_status == 'pending':
            query = query.filter(approved_for_training__isnull=True)
        elif review_status == 'approved':
            query = query.filter(approved_for_training=True)
        elif review_status == 'rejected':
            query = query.filter(approved_for_training=False)
        
        # 정렬
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
        query = query.order_by(sort_by)
        
        potholes = query[:limit]
        
        result = [{
            'id': p.id,
            'latitude': float(p.latitude),
            'longitude': float(p.longitude),
            'depth_ratio': float(p.depth_ratio),
            'validation_result': p.validation_result,
            'detected_at': p.detected_at.isoformat() if p.detected_at else None,
            'image_path': p.image_path,
            'confidence_score': float(p.confidence_score) if p.confidence_score else None,
            'priority_score': float(p.priority_score) if p.priority_score else None,
            'risk_level': p.risk_level,
            'location_type': p.location_type,
            'location_description': p.location_description,
            'bbox_x1': p.bbox_x1,
            'bbox_y1': p.bbox_y1,
            'bbox_x2': p.bbox_x2,
            'bbox_y2': p.bbox_y2,
            'approved_for_training': p.approved_for_training,
            'review_notes': getattr(p, 'review_notes', None),
            'reviewed_by_id': p.reviewed_by_id,
            'reviewed_at': p.reviewed_at.isoformat() if p.reviewed_at else None
        } for p in potholes]
        
        return jsonify({
            'count': len(result),
            'potholes': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/shared_images/<path:filename>')
def shared_images(filename):
    """공유 이미지 서빙 (이미지 미리보기 지원)"""
    try:
        # 이미지 파일인지 확인
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            return send_from_directory('/var/www/html/shared_images', filename)
        else:
            return send_from_directory('/var/www/html/shared_images', filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/image/<int:pothole_id>')
def get_pothole_image(pothole_id):
    """포트홀 이미지 조회 API (미리보기용)"""
    try:
        if not DJANGO_AVAILABLE:
            return jsonify({'error': 'Django not available'}), 500
        
        pothole = Pothole.objects.get(id=pothole_id)
        if not pothole.image_path:
            return jsonify({'error': 'Image path not found'}), 404
        
        # 이미지 경로 정규화
        img_path = pothole.image_path
        if not os.path.isabs(img_path):
            img_path = os.path.join('/var/www/html/shared_images', os.path.basename(img_path))
        elif not os.path.exists(img_path):
            img_path = os.path.join('/var/www/html/shared_images', os.path.basename(pothole.image_path))
        
        if os.path.exists(img_path):
            return send_from_directory(os.path.dirname(img_path), os.path.basename(img_path))
        else:
            return jsonify({'error': 'Image file not found'}), 404
    except Pothole.DoesNotExist:
        return jsonify({'error': 'Pothole not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 인증 API
@app.route('/api/auth/login', methods=['POST'])
def login():
    """로그인 API"""
    if not AUTH_AVAILABLE:
        return jsonify({'error': 'Auth module not available'}), 503
    
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = authenticate_user(username, password)
        if user:
            session['authenticated'] = True
            session['user'] = user
            return jsonify({
                'success': True,
                'user': user
            })
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """로그아웃 API"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """인증 상태 확인 API"""
    if not AUTH_AVAILABLE:
        return jsonify({'authenticated': False, 'user': None})
    
    authenticated = check_authentication()
    user = get_current_user() if authenticated else None
    return jsonify({
        'authenticated': authenticated,
        'user': user,
        'is_admin': is_admin() if authenticated else False
    })

# Phi-3 챗봇 API
@app.route('/api/chat', methods=['POST'])
def chat():
    """Phi-3 챗봇 API (고급 기능 지원)"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        use_advanced = data.get('use_advanced', True)  # 고급 기능 사용 여부
        max_tokens = data.get('max_tokens', 200)
        temperature = data.get('temperature', 0.7)
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # 고급 챗봇 사용
        if use_advanced and ADVANCED_CHATBOT_AVAILABLE:
            try:
                advanced_chatbot = get_advanced_chatbot()
                result = advanced_chatbot.answer_question(message)
                if result.get('success'):
                    return jsonify({
                        'success': True,
                        'response': result['response'],
                        'context_used': result.get('context_used', False),
                        'type': 'advanced'
                    })
            except Exception as e:
                print(f"[WARNING] Advanced chatbot failed, falling back to basic: {e}")
        
        # 기본 챗봇 사용
        if PHI3_AVAILABLE:
            chatbot = get_chatbot()
            if chatbot and chatbot.is_model_loaded():
                response = chatbot.generate_response(message, max_tokens=max_tokens, temperature=temperature)
                return jsonify({
                    'success': True,
                    'response': response,
                    'device': chatbot.device,
                    'type': 'basic'
                })
        
        return jsonify({'error': 'Chatbot not available'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/load_model', methods=['POST'])
def load_chatbot_model():
    """Phi-3 모델 로드 API"""
    if not PHI3_AVAILABLE:
        return jsonify({'error': 'Phi-3 chatbot not available'}), 503
    
    try:
        data = request.get_json() or {}
        model_path = data.get('model_path', os.getenv('PHI3_MODEL_PATH', '/app/models/llm/Phi-3-mini-int4'))
        device = data.get('device', os.getenv('PHI3_DEVICE', 'NPU'))
        
        chatbot = get_chatbot()
        if chatbot:
            chatbot.load_model(model_path, device)
        else:
            from phi3_chatbot import Phi3Chatbot
            chatbot = Phi3Chatbot(model_path=model_path, device=device)
            chatbot.load_model(model_path, device)
        
        return jsonify({
            'success': True,
            'model_path': chatbot.model_path,
            'device': chatbot.device,
            'loaded': chatbot.is_model_loaded()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 통계 API
@app.route('/api/statistics', methods=['GET'])
def statistics():
    """통계 데이터 조회 API"""
    if not STATISTICS_AVAILABLE:
        return jsonify({'error': 'Statistics module not available'}), 503
    
    try:
        days = request.args.get('days', 0, type=int)
        min_priority = request.args.get('min_priority', 0.0, type=float)
        risk_levels = request.args.getlist('risk_level')
        location_types = request.args.getlist('location_type')
        
        stats = get_statistics(days=days, min_priority=min_priority, 
                              risk_levels=risk_levels, location_types=location_types)
        
        if 'error' in stats:
            return jsonify(stats), 500
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 데이터 내보내기 API
@app.route('/api/export', methods=['GET'])
def export_data():
    """데이터 내보내기 API (CSV, JSON)"""
    try:
        if not DJANGO_AVAILABLE:
            return jsonify({'error': 'Django not available'}), 500
        
        format_type = request.args.get('format', 'json').lower()
        limit = request.args.get('limit', 1000, type=int)
        validated_only = request.args.get('validated', 'false').lower() == 'true'
        days = request.args.get('days', 0, type=int)
        
        # 데이터 조회
        query = Pothole.objects.all()
        
        if days > 0:
            start_date = datetime.now().date() - timedelta(days=days)
            query = query.filter(detected_at__date__gte=start_date)
        
        if validated_only:
            query = query.filter(validation_result=True)
        
        potholes = query.order_by('-detected_at')[:limit]
        
        # 데이터 변환
        data = [{
            'id': p.id,
            'latitude': float(p.latitude),
            'longitude': float(p.longitude),
            'depth_ratio': float(p.depth_ratio),
            'validation_result': p.validation_result,
            'detected_at': p.detected_at.isoformat() if p.detected_at else None,
            'image_path': p.image_path,
            'confidence_score': float(p.confidence_score) if p.confidence_score else None,
            'priority_score': float(p.priority_score) if p.priority_score else None,
            'risk_level': p.risk_level,
            'location_type': p.location_type,
            'location_description': p.location_description
        } for p in potholes]
        
        if format_type == 'csv':
            # CSV 생성
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=potholes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            return response
        else:
            # JSON
            response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=potholes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 관리자 검토 페이지 (관리자 인증 필요)
@app.route('/admin/review')
@admin_required
def admin_review_page():
    """관리자 검토 페이지"""
    return render_template('admin_review.html')

# 관리자 검토 API (관리자 인증 필요)
@app.route('/api/admin/review', methods=['GET'])
@admin_required
def admin_review_list():
    """관리자 검토 목록 조회"""
    try:
        if not DJANGO_AVAILABLE:
            return jsonify({'error': 'Django not available'}), 500
        
        limit = request.args.get('limit', 20, type=int)
        review_status = request.args.get('review_status', 'all')
        validation_status = request.args.get('validation_status', 'all')
        
        query = Pothole.objects.all()
        
        # 검토 상태 필터
        if review_status == 'pending':
            query = query.filter(approved_for_training__isnull=True)
        elif review_status == 'approved':
            query = query.filter(approved_for_training=True)
        elif review_status == 'rejected':
            query = query.filter(approved_for_training=False)
        
        # 검증 상태 필터
        if validation_status == 'validated':
            query = query.filter(validation_result=True)
        elif validation_status == 'not_validated':
            query = query.filter(validation_result=False)
        
        potholes = query.order_by('-detected_at')[:limit]
        
        result = [{
            'id': p.id,
            'latitude': float(p.latitude),
            'longitude': float(p.longitude),
            'depth_ratio': float(p.depth_ratio),
            'validation_result': p.validation_result,
            'detected_at': p.detected_at.isoformat() if p.detected_at else None,
            'image_path': p.image_path,
            'confidence_score': float(p.confidence_score) if p.confidence_score else None,
            'priority_score': float(p.priority_score) if p.priority_score else None,
            'risk_level': p.risk_level,
            'location_type': p.location_type,
            'location_description': p.location_description,
            'bbox_x1': p.bbox_x1,
            'bbox_y1': p.bbox_y1,
            'bbox_x2': p.bbox_x2,
            'bbox_y2': p.bbox_y2,
            'approved_for_training': p.approved_for_training,
            'review_notes': getattr(p, 'review_notes', None),
            'reviewed_by_id': p.reviewed_by_id,
            'reviewed_at': p.reviewed_at.isoformat() if p.reviewed_at else None
        } for p in potholes]
        
        return jsonify({
            'count': len(result),
            'potholes': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/review/<int:pothole_id>/approve', methods=['POST'])
@admin_required
def approve_pothole(pothole_id):
    """포트홀 승인"""
    try:
        if not DJANGO_AVAILABLE:
            return jsonify({'error': 'Django not available'}), 500
        
        data = request.get_json() or {}
        note = data.get('note', '')
        
        pothole = Pothole.objects.get(id=pothole_id)
        pothole.approved_for_training = True
        if hasattr(pothole, 'review_notes'):
            pothole.review_notes = note
        # 관리자 인증이 필요하므로 사용자 정보 저장
        user = get_current_user()
        if user:
            pothole.reviewed_by_id = user['id']
        from datetime import datetime
        pothole.reviewed_at = datetime.now()
        pothole.save()
        
        return jsonify({'success': True})
    except Pothole.DoesNotExist:
        return jsonify({'error': 'Pothole not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/review/<int:pothole_id>/reject', methods=['POST'])
@admin_required
def reject_pothole(pothole_id):
    """포트홀 거부"""
    try:
        if not DJANGO_AVAILABLE:
            return jsonify({'error': 'Django not available'}), 500
        
        data = request.get_json() or {}
        note = data.get('note', '')
        
        pothole = Pothole.objects.get(id=pothole_id)
        pothole.approved_for_training = False
        if hasattr(pothole, 'review_notes'):
            pothole.review_notes = note
        # 관리자 인증이 필요하므로 사용자 정보 저장
        user = get_current_user()
        if user:
            pothole.reviewed_by_id = user['id']
        from datetime import datetime
        pothole.reviewed_at = datetime.now()
        pothole.save()
        
        return jsonify({'success': True})
    except Pothole.DoesNotExist:
        return jsonify({'error': 'Pothole not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 비디오 결과 API
@app.route('/api/video-results', methods=['GET'])
def video_results():
    """비디오 결과 목록 조회"""
    try:
        video_results_dir = '/var/www/html/shared_images/video_results'
        
        if not os.path.exists(video_results_dir):
            return jsonify({'videos': []})
        
        videos = []
        for item in os.listdir(video_results_dir):
            item_path = os.path.join(video_results_dir, item)
            if os.path.isdir(item_path):
                info_file = os.path.join(item_path, 'video_info.json')
                if os.path.exists(info_file):
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            video_info = json.load(f)
                            video_info['directory'] = item
                            videos.append(video_info)
                    except:
                        pass
        
        # 정렬 (처리 중인 것 먼저, 그 다음 최신순)
        videos.sort(key=lambda x: (
            0 if x.get('status') == 'processing' else 1,
            x.get('start_time', '')
        ), reverse=True)
        
        return jsonify({'videos': videos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/video-results/<path:directory>', methods=['GET'])
def video_result_detail(directory):
    """비디오 결과 상세 조회"""
    try:
        video_results_dir = '/var/www/html/shared_images/video_results'
        info_file = os.path.join(video_results_dir, directory, 'video_info.json')
        
        if not os.path.exists(info_file):
            return jsonify({'error': 'Video result not found'}), 404
        
        with open(info_file, 'r', encoding='utf-8') as f:
            video_info = json.load(f)
            video_info['directory'] = directory
            
            # 동영상 파일 경로 확인
            result_dir = os.path.join(video_results_dir, directory)
            if 'result_video_path' not in video_info or not os.path.exists(video_info.get('result_video_path', '')):
                # 자동 검색
                video_basename = os.path.splitext(video_info.get('video_name', ''))[0]
                if video_basename:
                    possible_path = os.path.join(result_dir, f"{video_basename}_result.mp4")
                    if os.path.exists(possible_path):
                        video_info['result_video_path'] = possible_path
            
            return jsonify(video_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

