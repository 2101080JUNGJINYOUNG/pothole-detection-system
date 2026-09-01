-- 포트홀 데이터 재분배 및 위험도 재계산 SQL 스크립트
-- 서울 지역 내 다양한 위치로 분산하고 위치 유형별 위험도 할당

-- 1. 기존 데이터의 위치를 서울 지역 내 다양한 위치로 분산
-- 2. 각 데이터에 위치 유형 할당
-- 3. 우선순위 점수 및 위험도 레벨 재계산

DO $$
DECLARE
    pothole_record RECORD;
    new_lat DECIMAL(10, 8);
    new_lon DECIMAL(11, 8);
    location_type_val VARCHAR(50);
    location_desc_val VARCHAR(200);
    location_weight DECIMAL(5, 2);
    priority_score_val DECIMAL(10, 4);
    risk_level_val VARCHAR(20);
    depth_score DECIMAL(10, 4);
    validation_score DECIMAL(10, 4);
    base_lat DECIMAL(10, 8) := 37.5665;  -- 서울 중심 위도
    base_lon DECIMAL(11, 8) := 126.9780; -- 서울 중심 경도
    location_types TEXT[] := ARRAY['highway', 'school_zone', 'school_area', 'hospital_area', 
                                  'bus_lane', 'residential', 'commercial', 'general', 'park'];
    location_weights DECIMAL[] := ARRAY[3.0, 3.0, 2.5, 2.5, 2.0, 1.2, 1.0, 1.0, 0.8];
    location_names TEXT[] := ARRAY['고속도로', '어린이 보호구역', '학교 주변', '병원 주변',
                                   '시내버스 전용차로', '주거 지역', '상업 지역', '일반 도로', '공원/녹지'];
    type_idx INTEGER;
    counter INTEGER := 0;
BEGIN
    -- 각 포트홀 데이터 처리
    FOR pothole_record IN SELECT id, latitude, longitude, depth_ratio, validation_result FROM potholes
    LOOP
        counter := counter + 1;
        
        -- 서울 지역 내 랜덤 위치 생성 (약 20km 반경)
        new_lat := base_lat + (RANDOM() * 0.3 - 0.15);  -- ±0.15도 (약 ±17km)
        new_lon := base_lon + (RANDOM() * 0.3 - 0.15);
        
        -- 위치 유형 선택 (가중치에 따라 고위험 지역에 더 많이 할당)
        -- 가중치가 높을수록 선택 확률이 높음
        type_idx := 1 + (RANDOM() * 9)::INTEGER;
        -- 더 정확한 가중치 기반 선택을 위해 간단한 랜덤 사용
        type_idx := CASE 
            WHEN RANDOM() < 0.3 THEN 1  -- highway (30%)
            WHEN RANDOM() < 0.5 THEN 2  -- school_zone (20%)
            WHEN RANDOM() < 0.65 THEN 3 -- school_area (15%)
            WHEN RANDOM() < 0.75 THEN 4 -- hospital_area (10%)
            WHEN RANDOM() < 0.82 THEN 5 -- bus_lane (7%)
            WHEN RANDOM() < 0.88 THEN 6 -- residential (6%)
            WHEN RANDOM() < 0.93 THEN 7 -- commercial (5%)
            WHEN RANDOM() < 0.98 THEN 8 -- general (5%)
            ELSE 9                     -- park (2%)
        END;
        
        location_type_val := location_types[type_idx];
        location_desc_val := location_names[type_idx];
        location_weight := location_weights[type_idx];
        
        -- 우선순위 점수 계산
        -- priority_score = (location_weight * 10) + (depth_ratio * 0.3 * 10) + (validation_result * 0.2 * 10)
        depth_score := pothole_record.depth_ratio * 0.3 * 10;
        validation_score := CASE WHEN pothole_record.validation_result THEN 1.0 * 0.2 * 10 ELSE 0.0 END;
        priority_score_val := (location_weight * 10) + depth_score + validation_score;
        
        -- 위험도 레벨 결정
        risk_level_val := CASE
            WHEN priority_score_val >= 30 THEN 'critical'
            WHEN priority_score_val >= 20 THEN 'high'
            WHEN priority_score_val >= 10 THEN 'medium'
            ELSE 'low'
        END;
        
        -- 데이터 업데이트
        UPDATE potholes
        SET latitude = new_lat,
            longitude = new_lon,
            location_type = location_type_val,
            risk_level = risk_level_val,
            priority_score = priority_score_val,
            location_description = location_desc_val
        WHERE id = pothole_record.id;
        
        -- 진행 상황 출력 (10개마다)
        IF counter % 10 = 0 THEN
            RAISE NOTICE '진행 중... % 개 처리됨', counter;
        END IF;
    END LOOP;
    
    RAISE NOTICE '완료: 총 % 개의 데이터가 업데이트되었습니다.', counter;
END $$;

-- 통계 조회
SELECT 
    location_type,
    location_description,
    risk_level,
    COUNT(*) as count,
    ROUND(AVG(priority_score), 2) as avg_priority,
    ROUND(MIN(priority_score), 2) as min_priority,
    ROUND(MAX(priority_score), 2) as max_priority
FROM potholes
GROUP BY location_type, location_description, risk_level
ORDER BY avg_priority DESC;



