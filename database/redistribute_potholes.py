"""
기존 포트홀 데이터를 다양한 위치로 재분배하고 위험도를 재계산하는 스크립트
"""

import psycopg2
import random
import json
import os

# 데이터베이스 연결
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="pothole_db",
        user="pothole_user",
        password="pothole_pass",
        port=5432
    )

# 위험도 설정 로드
def load_risk_zones():
    risk_zones_path = "risk_zones.json"
    if os.path.exists(risk_zones_path):
        with open(risk_zones_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "risk_zones": [
            {"type": "highway", "priority_weight": 3.0, "name": "고속도로"},
            {"type": "school_zone", "priority_weight": 3.0, "name": "어린이 보호구역"},
            {"type": "school_area", "priority_weight": 2.5, "name": "학교 주변"},
            {"type": "hospital_area", "priority_weight": 2.5, "name": "병원 주변"},
            {"type": "bus_lane", "priority_weight": 2.0, "name": "시내버스 전용차로"},
            {"type": "residential", "priority_weight": 1.2, "name": "주거 지역"},
            {"type": "commercial", "priority_weight": 1.0, "name": "상업 지역"},
            {"type": "general", "priority_weight": 1.0, "name": "일반 도로"},
            {"type": "park", "priority_weight": 0.8, "name": "공원/녹지"}
        ],
        "default_priority_weight": 1.0,
        "depth_weight": 0.3,
        "validation_weight": 0.2
    }

# 우선순위 점수 계산
def calculate_priority_score(location_weight, depth_ratio, validation_result, config):
    depth_weight = config.get('depth_weight', 0.3)
    validation_weight = config.get('validation_weight', 0.2)
    
    depth_score = depth_ratio * depth_weight * 10
    validation_score = 1.0 if validation_result else 0.0
    
    priority_score = (
        location_weight * 10 +
        depth_score +
        validation_score * validation_weight * 10
    )
    
    return round(priority_score, 4)

# 위험도 레벨 결정
def determine_risk_level(priority_score):
    if priority_score >= 30:
        return 'critical'
    elif priority_score >= 20:
        return 'high'
    elif priority_score >= 10:
        return 'medium'
    else:
        return 'low'

# 서울 지역 내 다양한 위치 생성
def generate_diverse_locations(count):
    """서울 지역 내 다양한 위치 생성"""
    # 서울 중심 좌표
    base_lat = 37.5665
    base_lon = 126.9780
    
    locations = []
    for i in range(count):
        # 서울 지역 내 랜덤 위치 생성 (약 20km 반경)
        lat_offset = random.uniform(-0.15, 0.15)  # 약 ±17km
        lon_offset = random.uniform(-0.15, 0.15)  # 약 ±17km
        
        lat = base_lat + lat_offset
        lon = base_lon + lon_offset
        
        locations.append((lat, lon))
    
    return locations

def main():
    print("=" * 60)
    print("포트홀 데이터 재분배 및 위험도 재계산")
    print("=" * 60)
    
    # 데이터베이스 연결
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 기존 데이터 조회
    cursor.execute("SELECT id, latitude, longitude, depth_ratio, validation_result FROM potholes")
    potholes = cursor.fetchall()
    
    print(f"\n총 {len(potholes)}개의 포트홀 데이터를 처리합니다.")
    
    if len(potholes) == 0:
        print("처리할 데이터가 없습니다.")
        return
    
    # 위험도 설정 로드
    config = load_risk_zones()
    risk_zones = config['risk_zones']
    
    # 위치 유형별 이름 매핑
    location_type_map = {zone['type']: zone['name'] for zone in risk_zones}
    location_weight_map = {zone['type']: zone['priority_weight'] for zone in risk_zones}
    
    # 다양한 위치 생성
    new_locations = generate_diverse_locations(len(potholes))
    
    # 위치 유형 분배 (고위험 지역에 더 많은 데이터 할당)
    location_types = []
    for i in range(len(potholes)):
        # 가중치에 따라 위치 유형 선택 (고위험 지역에 더 많이 할당)
        weights = [zone['priority_weight'] for zone in risk_zones]
        location_type = random.choices(
            [zone['type'] for zone in risk_zones],
            weights=weights,
            k=1
        )[0]
        location_types.append(location_type)
    
    # 데이터 업데이트
    updated_count = 0
    for i, (pothole_id, old_lat, old_lon, depth_ratio, validation_result) in enumerate(potholes):
        # 새로운 위치
        new_lat, new_lon = new_locations[i]
        
        # 위치 유형
        location_type = location_types[i]
        location_description = location_type_map.get(location_type, '일반 도로')
        location_weight = location_weight_map.get(location_type, 1.0)
        
        # 우선순위 점수 계산
        priority_score = calculate_priority_score(
            location_weight, depth_ratio, validation_result, config
        )
        
        # 위험도 레벨 결정
        risk_level = determine_risk_level(priority_score)
        
        # 데이터베이스 업데이트
        try:
            cursor.execute("""
                UPDATE potholes
                SET latitude = %s,
                    longitude = %s,
                    location_type = %s,
                    risk_level = %s,
                    priority_score = %s,
                    location_description = %s
                WHERE id = %s
            """, (new_lat, new_lon, location_type, risk_level, priority_score, 
                  location_description, pothole_id))
            
            updated_count += 1
            if (i + 1) % 10 == 0:
                print(f"진행 중... {i + 1}/{len(potholes)}")
        except Exception as e:
            print(f"오류 발생 (ID: {pothole_id}): {str(e)}")
            conn.rollback()
            continue
    
    # 커밋
    conn.commit()
    
    print(f"\n✅ 완료: {updated_count}개의 데이터가 업데이트되었습니다.")
    
    # 통계 출력
    cursor.execute("""
        SELECT 
            location_type,
            risk_level,
            COUNT(*) as count,
            AVG(priority_score) as avg_priority
        FROM potholes
        GROUP BY location_type, risk_level
        ORDER BY avg_priority DESC
    """)
    
    stats = cursor.fetchall()
    print("\n📊 위치 유형별 통계:")
    print("-" * 60)
    for location_type, risk_level, count, avg_priority in stats:
        location_name = location_type_map.get(location_type, location_type)
        print(f"{location_name:20s} | {risk_level:10s} | {count:3d}개 | 평균 우선순위: {avg_priority:.2f}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("재분배 완료! 대시보드에서 확인하세요.")
    print("=" * 60)

if __name__ == "__main__":
    main()



