-- 위험도 필드 추가 마이그레이션 스크립트
-- 기존 테이블에 위험도 관련 필드 추가

-- 위험도 레벨 필드 추가
ALTER TABLE potholes 
ADD COLUMN IF NOT EXISTS location_type VARCHAR(50) DEFAULT 'general',
ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'medium',
ADD COLUMN IF NOT EXISTS priority_score DECIMAL(10, 4) DEFAULT 1.0,
ADD COLUMN IF NOT EXISTS location_description VARCHAR(200);

-- 우선순위 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_potholes_priority ON potholes(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_potholes_risk_level ON potholes(risk_level);
CREATE INDEX IF NOT EXISTS idx_potholes_location_type ON potholes(location_type);

-- 기존 데이터의 우선순위 점수 업데이트 (기본값)
UPDATE potholes 
SET priority_score = 1.0 
WHERE priority_score IS NULL OR priority_score = 0;

-- 뷰 업데이트 (우선순위 높은 포트홀)
CREATE OR REPLACE VIEW high_priority_potholes AS
SELECT * FROM potholes 
WHERE validation_result = true 
  AND priority_score >= 2.0
ORDER BY priority_score DESC, detected_at DESC;

-- 뷰 업데이트 (위험도 높은 포트홀)
CREATE OR REPLACE VIEW high_risk_potholes AS
SELECT * FROM potholes 
WHERE validation_result = true 
  AND risk_level IN ('high', 'critical')
ORDER BY priority_score DESC, detected_at DESC;



