-- Deep-Guardian 포트홀 데이터베이스 초기화 스크립트 (MySQL)

-- 데이터베이스 생성 (이미 존재하는 경우 무시)
CREATE DATABASE IF NOT EXISTS pothole_db;
USE pothole_db;

-- 포트홀 테이블 생성
CREATE TABLE IF NOT EXISTS potholes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    depth_ratio DECIMAL(5, 4) NOT NULL,
    validation_result BOOLEAN NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_path VARCHAR(500),
    bbox_x1 INT,
    bbox_y1 INT,
    bbox_x2 INT,
    bbox_y2 INT,
    confidence_score DECIMAL(5, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_location (latitude, longitude),
    INDEX idx_detected_at (detected_at DESC),
    INDEX idx_validation (validation_result)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 뷰 생성 (검증 통과한 포트홀만)
CREATE OR REPLACE VIEW validated_potholes AS
SELECT * FROM potholes WHERE validation_result = true;

-- 사용자 테이블 (인증 시스템용)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 샘플 데이터 (테스트용, 선택사항)
-- INSERT INTO potholes (latitude, longitude, depth_ratio, validation_result, image_path)
-- VALUES 
--     (37.5665, 126.9780, 0.45, true, '/shared_images/sample1.jpg'),
--     (37.5651, 126.9895, 0.32, true, '/shared_images/sample2.jpg'),
--     (37.5660, 126.9770, 0.28, false, '/shared_images/sample3.jpg');

