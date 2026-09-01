-- 포트홀 데이터 재분배 및 위험도 재계산 SQL 스크립트 (수정 버전)

-- 1단계: 위치를 서울 지역 내 다양한 위치로 분산
UPDATE potholes
SET 
    latitude = 37.5665 + (RANDOM() * 0.3 - 0.15),
    longitude = 126.9780 + (RANDOM() * 0.3 - 0.15)
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- 2단계: 위치 유형 할당 및 위험도 재계산
UPDATE potholes
SET 
    location_type = CASE 
        WHEN RANDOM() < 0.15 THEN 'highway'
        WHEN RANDOM() < 0.30 THEN 'school_zone'
        WHEN RANDOM() < 0.45 THEN 'school_area'
        WHEN RANDOM() < 0.55 THEN 'hospital_area'
        WHEN RANDOM() < 0.65 THEN 'bus_lane'
        WHEN RANDOM() < 0.75 THEN 'residential'
        WHEN RANDOM() < 0.85 THEN 'commercial'
        WHEN RANDOM() < 0.95 THEN 'general'
        ELSE 'park'
    END,
    location_description = CASE 
        WHEN RANDOM() < 0.15 THEN 'Highway'
        WHEN RANDOM() < 0.30 THEN 'School Zone'
        WHEN RANDOM() < 0.45 THEN 'School Area'
        WHEN RANDOM() < 0.55 THEN 'Hospital Area'
        WHEN RANDOM() < 0.65 THEN 'Bus Lane'
        WHEN RANDOM() < 0.75 THEN 'Residential'
        WHEN RANDOM() < 0.85 THEN 'Commercial'
        WHEN RANDOM() < 0.95 THEN 'General Road'
        ELSE 'Park'
    END
WHERE location_type IS NULL OR location_type = 'general';

-- 3단계: 우선순위 점수 및 위험도 재계산
UPDATE potholes
SET 
    priority_score = (
        CASE location_type
            WHEN 'highway' THEN 3.0
            WHEN 'school_zone' THEN 3.0
            WHEN 'school_area' THEN 2.5
            WHEN 'hospital_area' THEN 2.5
            WHEN 'bus_lane' THEN 2.0
            WHEN 'residential' THEN 1.2
            WHEN 'commercial' THEN 1.0
            WHEN 'general' THEN 1.0
            WHEN 'park' THEN 0.8
            ELSE 1.0
        END * 10
    ) + (depth_ratio * 0.3 * 10) + (CASE WHEN validation_result THEN 1.0 * 0.2 * 10 ELSE 0.0 END),
    risk_level = CASE
        WHEN (
            (CASE location_type
                WHEN 'highway' THEN 3.0
                WHEN 'school_zone' THEN 3.0
                WHEN 'school_area' THEN 2.5
                WHEN 'hospital_area' THEN 2.5
                WHEN 'bus_lane' THEN 2.0
                WHEN 'residential' THEN 1.2
                WHEN 'commercial' THEN 1.0
                WHEN 'general' THEN 1.0
                WHEN 'park' THEN 0.8
                ELSE 1.0
            END * 10) + (depth_ratio * 0.3 * 10) + (CASE WHEN validation_result THEN 1.0 * 0.2 * 10 ELSE 0.0 END)
        ) >= 30 THEN 'critical'
        WHEN (
            (CASE location_type
                WHEN 'highway' THEN 3.0
                WHEN 'school_zone' THEN 3.0
                WHEN 'school_area' THEN 2.5
                WHEN 'hospital_area' THEN 2.5
                WHEN 'bus_lane' THEN 2.0
                WHEN 'residential' THEN 1.2
                WHEN 'commercial' THEN 1.0
                WHEN 'general' THEN 1.0
                WHEN 'park' THEN 0.8
                ELSE 1.0
            END * 10) + (depth_ratio * 0.3 * 10) + (CASE WHEN validation_result THEN 1.0 * 0.2 * 10 ELSE 0.0 END)
        ) >= 20 THEN 'high'
        WHEN (
            (CASE location_type
                WHEN 'highway' THEN 3.0
                WHEN 'school_zone' THEN 3.0
                WHEN 'school_area' THEN 2.5
                WHEN 'hospital_area' THEN 2.5
                WHEN 'bus_lane' THEN 2.0
                WHEN 'residential' THEN 1.2
                WHEN 'commercial' THEN 1.0
                WHEN 'general' THEN 1.0
                WHEN 'park' THEN 0.8
                ELSE 1.0
            END * 10) + (depth_ratio * 0.3 * 10) + (CASE WHEN validation_result THEN 1.0 * 0.2 * 10 ELSE 0.0 END)
        ) >= 10 THEN 'medium'
        ELSE 'low'
    END
WHERE priority_score IS NULL OR priority_score = 0;

-- 통계 조회
SELECT 
    location_type,
    risk_level,
    COUNT(*) as count,
    ROUND(AVG(priority_score), 2) as avg_priority,
    ROUND(MIN(priority_score), 2) as min_priority,
    ROUND(MAX(priority_score), 2) as max_priority
FROM potholes
GROUP BY location_type, risk_level
ORDER BY avg_priority DESC;



