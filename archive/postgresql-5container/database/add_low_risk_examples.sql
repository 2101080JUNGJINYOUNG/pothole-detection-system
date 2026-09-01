-- Low 레벨 예제 3개 추가 생성
-- 우선순위 점수가 낮은 데이터 중 3개를 Low로 설정

UPDATE potholes
SET 
    risk_level = 'low',
    priority_score = 5.0  -- Low 레벨에 적합한 점수
WHERE id IN (
    SELECT id FROM potholes
    WHERE risk_level = 'medium' 
      AND priority_score <= 1.0
    ORDER BY priority_score ASC, id
    LIMIT 3
);

-- Medium 레벨이 너무 많으므로 일부를 Low로 변경
-- 우선순위 점수가 가장 낮은 Medium 데이터 3개를 Low로 변경
UPDATE potholes
SET 
    risk_level = 'low',
    priority_score = 5.0
WHERE id IN (
    SELECT id FROM potholes
    WHERE risk_level = 'medium'
      AND priority_score = 1.0
    ORDER BY id
    LIMIT 3
);

-- 결과 확인
SELECT 
    risk_level,
    COUNT(*) as count,
    ROUND(AVG(priority_score), 2) as avg_priority,
    ROUND(MIN(priority_score), 2) as min_priority,
    ROUND(MAX(priority_score), 2) as max_priority
FROM potholes
GROUP BY risk_level
ORDER BY 
    CASE risk_level
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        ELSE 5
    END;

-- 각 레벨별 샘플 데이터 확인
SELECT 
    id,
    risk_level,
    ROUND(priority_score, 2) as priority,
    location_description,
    ROUND(depth_ratio, 3) as depth_ratio
FROM potholes
WHERE risk_level IN ('critical', 'high', 'medium', 'low')
ORDER BY 
    CASE risk_level
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    priority_score DESC
LIMIT 12;



