"""
Deep-Guardian Flask Dashboard
Apache에서 실행되는 데이터 시각화 대시보드
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import psycopg2
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import bcrypt

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'deep-guardian-secret-key-change-in-production')

# 데이터베이스 연결
def get_db_connection():
    """데이터베이스 연결"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'db'),
            database=os.getenv('DB_NAME', 'pothole_db'),
            user=os.getenv('DB_USER', 'pothole_user'),
            password=os.getenv('DB_PASSWORD', 'pothole_pass'),
            port=int(os.getenv('DB_PORT', '5432'))
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# 인증 확인
def check_auth():
    """인증 확인"""
    return 'user_id' in session

def is_admin():
    """관리자 확인"""
    if not check_auth():
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = %s", (session['user_id'],))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result and result[0] == 'admin'
    except:
        return False

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            return render_template('login.html', error='데이터베이스 연결 실패')
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error='사용자명 또는 비밀번호가 잘못되었습니다')
        except Exception as e:
            return render_template('login.html', error=f'로그인 오류: {str(e)}')
    
    return render_template('login.html')

# 로그아웃
@app.route('/logout')
def logout():
    """로그아웃"""
    session.clear()
    return redirect(url_for('login'))

# 메인 대시보드
@app.route('/')
def index():
    """메인 대시보드"""
    if not check_auth():
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

# API: 통계 데이터
@app.route('/api/statistics')
def api_statistics():
    """통계 데이터 API"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        query = """
        SELECT 
            COUNT(*) as total_count,
            COUNT(CASE WHEN validation_result = true THEN 1 END) as validated_count,
            AVG(depth_ratio) as avg_depth_ratio,
            MAX(detected_at) as last_detection
        FROM potholes
        WHERE approved_for_training = true
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            stats = {
                'total_count': int(df.iloc[0]['total_count']),
                'validated_count': int(df.iloc[0]['validated_count']),
                'avg_depth_ratio': float(df.iloc[0]['avg_depth_ratio']) if df.iloc[0]['avg_depth_ratio'] else 0,
                'last_detection': df.iloc[0]['last_detection'].isoformat() if df.iloc[0]['last_detection'] else None
            }
            return jsonify(stats)
        else:
            return jsonify({
                'total_count': 0,
                'validated_count': 0,
                'avg_depth_ratio': 0,
                'last_detection': None
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 포트홀 데이터
@app.route('/api/potholes')
def api_potholes():
    """포트홀 데이터 API"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        limit = request.args.get('limit', 100, type=int)
        days = request.args.get('days', 30, type=int)
        
        query = """
        SELECT 
            id, latitude, longitude, depth_ratio, 
            validation_result, detected_at, image_path,
            location_type, risk_level, priority_score, location_description
        FROM potholes
        WHERE approved_for_training = true
        AND detected_at >= NOW() - INTERVAL '%s days'
        ORDER BY priority_score DESC, detected_at DESC
        LIMIT %s
        """
        df = pd.read_sql_query(query, conn, params=(days, limit))
        conn.close()
        
        # DataFrame을 JSON으로 변환
        df['detected_at'] = df['detected_at'].astype(str)
        return jsonify(df.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: 위험도별 통계
@app.route('/api/risk_stats')
def api_risk_stats():
    """위험도별 통계 API"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        query = """
        SELECT 
            risk_level,
            COUNT(*) as count
        FROM potholes
        WHERE approved_for_training = true
        GROUP BY risk_level
        ORDER BY 
            CASE risk_level
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
                ELSE 5
            END
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return jsonify(df.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)



