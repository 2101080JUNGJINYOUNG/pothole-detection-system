-- 각 위험도 레벨별로 3개씩 예제 데이터 생성

-- 1. Critical 레벨 (3개)
-- 우선순위 점수가 높은 데이터 중 상위 3개를 Critical로 설정
UPDATE potholes
SET 
    risk_level = 'critical',
    priority_score = CASE
        WHEN priority_score < 30 THEN 35.0  -- Critical 최소값
        ELSE priority_score
    END
WHERE id IN (
    SELECT id FROM potholes
    ORDER BY priority_score DESC NULLS LAST, id
    LIMIT 3
);

-- 2. High 레벨 (3개)
-- Critical이 아닌 데이터 중 우선순위가 높은 3개를 High로 설정
UPDATE potholes
SET 
    risk_level = 'high',
    priority_score = CASE
        WHEN priority_score < 20 THEN 25.0  -- High 최소값
        WHEN priority_score >= 30 THEN 25.0  -- Critical 범위면 High 범위로 조정
        ELSE priority_score
    END
WHERE id IN (
    SELECT id FROM potholes
    WHERE risk_level != 'critical' OR risk_level IS NULL
    ORDER BY priority_score DESC NULLS LAST, id
    LIMIT 3
);

-- 3. Medium 레벨 (3개)
-- Critical, High가 아닌 데이터 중 3개를 Medium으로 설정
UPDATE potholes
SET 
    risk_level = 'medium',
    priority_score = CASE
        WHEN priority_score < 10 THEN 15.0  -- Medium 최소값
        WHEN priority_score >= 20 THEN 15.0  -- High 범위면 Medium 범위로 조정
        ELSE priority_score
    END
WHERE id IN (
    SELECT id FROM potholes
    WHERE (risk_level NOT IN ('critical', 'high') OR risk_level IS NULL)
    ORDER BY priority_score DESC NULLS LAST, id
    LIMIT 3
);

-- 4. Low 레벨 (3개)
-- 나머지 데이터 중 3개를 Low로 설정
UPDATE potholes
SET 
    risk_level = 'low',
    priority_score = CASE
        WHEN priority_score >= 10 THEN 8.0  -- Low 최대값
        WHEN priority_score IS NULL OR priority_score = 0 THEN 5.0
        ELSE priority_score
    END
WHERE id IN (
    SELECT id FROM potholes
    WHERE (risk_level NOT IN ('critical', 'high', 'medium') OR risk_level IS NULL)
    ORDER BY priority_score ASC NULLS LAST, id
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



