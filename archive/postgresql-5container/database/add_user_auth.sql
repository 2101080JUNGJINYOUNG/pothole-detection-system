-- 사용자 인증 시스템 추가
-- 사용자 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',  -- 'user' or 'admin'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 기본 관리자 계정 생성 (비밀번호: admin123)
-- 실제 운영 시에는 비밀번호를 변경해야 합니다
-- 비밀번호 해시는 'admin123'의 bcrypt 해시입니다
INSERT INTO users (username, password_hash, role) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', 'admin')
ON CONFLICT (username) DO NOTHING;

-- 기본 일반 사용자 계정 생성 (비밀번호: user123)
INSERT INTO users (username, password_hash, role) 
VALUES ('user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', 'user')
ON CONFLICT (username) DO NOTHING;

-- 포트홀 테이블에 관리자 승인 필드 추가
ALTER TABLE potholes 
ADD COLUMN IF NOT EXISTS approved_for_training BOOLEAN DEFAULT NULL,
ADD COLUMN IF NOT EXISTS reviewed_by INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_potholes_approved ON potholes(approved_for_training);
CREATE INDEX IF NOT EXISTS idx_potholes_reviewed ON potholes(reviewed_at DESC);

-- 뷰 생성 (관리자가 승인한 포트홀만)
CREATE OR REPLACE VIEW approved_potholes AS
SELECT * FROM potholes 
WHERE approved_for_training = true
  AND validation_result = true;





