-- Deep-Guardian 포트홀 데이터베이스 초기화 스크립트

-- 포트홀 테이블 생성
CREATE TABLE IF NOT EXISTS potholes (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    depth_ratio DECIMAL(5, 4) NOT NULL,
    validation_result BOOLEAN NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_path VARCHAR(500),
    bbox_x1 INTEGER,
    bbox_y1 INTEGER,
    bbox_x2 INTEGER,
    bbox_y2 INTEGER,
    confidence_score DECIMAL(5, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_potholes_location ON potholes(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_potholes_detected_at ON potholes(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_potholes_validation ON potholes(validation_result);

-- 뷰 생성 (검증 통과한 포트홀만)
CREATE OR REPLACE VIEW validated_potholes AS
SELECT * FROM potholes WHERE validation_result = true;

-- 사용자 인증 시스템 추가 (별도 스크립트 실행 필요)
-- \i add_user_auth.sql

-- 샘플 데이터 (테스트용, 선택사항)
-- INSERT INTO potholes (latitude, longitude, depth_ratio, validation_result, image_path)
-- VALUES 
--     (37.5665, 126.9780, 0.45, true, '/data/sample1.jpg'),
--     (37.5651, 126.9895, 0.32, true, '/data/sample2.jpg'),
--     (37.5660, 126.9770, 0.28, false, '/data/sample3.jpg');




