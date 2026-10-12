-- ====================================================================
-- Circadian Hydration Platform - PostgreSQL Database Schema & Seed DDL
-- 버전: 1.0.0 (MVP)
-- ====================================================================

-- 1. UUID 확장 모듈 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. 사용자 테이블 (users)
DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255),
    provider VARCHAR(50) DEFAULT 'email', -- 'email', 'kakao', 'naver', 'google'
    provider_id VARCHAR(255),
    nickname VARCHAR(100) DEFAULT '수분탐험가',
    gender VARCHAR(10) DEFAULT 'unspecified', -- 'male', 'female', 'other'
    age INT DEFAULT 30,
    height_cm NUMERIC(5, 2) DEFAULT 170.00,
    weight_kg NUMERIC(5, 2) DEFAULT 65.00,
    activity_level VARCHAR(50) DEFAULT 'moderate', -- 'sedentary', 'light', 'moderate', 'active', 'very_active'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- 3. 매일 아침 30초 체크 기록 테이블 (morning_checks)
DROP TABLE IF EXISTS morning_checks CASCADE;
CREATE TABLE morning_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    check_date DATE NOT NULL DEFAULT CURRENT_DATE,
    wake_time TIME NOT NULL,
    sleep_hours NUMERIC(4, 2) NOT NULL,
    thirst_level INT NOT NULL CHECK (thirst_level BETWEEN 1 AND 5),
    dry_mouth_level INT NOT NULL CHECK (dry_mouth_level BETWEEN 1 AND 5),
    urine_color INT NOT NULL CHECK (urine_color BETWEEN 1 AND 8),
    has_coffee_plan BOOLEAN DEFAULT FALSE,
    has_workout_plan BOOLEAN DEFAULT FALSE,
    hydration_score INT NOT NULL CHECK (hydration_score BETWEEN 0 AND 100),
    hydration_grade VARCHAR(20) NOT NULL, -- '매우 좋음', '좋음', '주의', '위험'
    recommended_ml INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_check_date UNIQUE (user_id, check_date)
);

CREATE INDEX idx_morning_checks_user_date ON morning_checks(user_id, check_date);

-- 4. 물 섭취 실시간 기록 테이블 (water_intake_logs)
DROP TABLE IF EXISTS water_intake_logs CASCADE;
CREATE TABLE water_intake_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_ml INT NOT NULL, -- 250, 500, 750, 1000 등
    log_date DATE NOT NULL DEFAULT CURRENT_DATE,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_water_logs_user_date ON water_intake_logs(user_id, log_date);
CREATE INDEX idx_water_logs_timestamp ON water_intake_logs(logged_at);

-- 5. 서카디언 제품 마스터 테이블 (products)
DROP TABLE IF EXISTS products CASCADE;
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    sub_title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    time_slot VARCHAR(20) NOT NULL, -- 'MORNING', 'DAY', 'EVENING', 'NIGHT'
    recommended_time VARCHAR(20) NOT NULL, -- '08:00', '13:00', '18:00', '22:00'
    key_ingredients VARCHAR(255) NOT NULL,
    purchase_url VARCHAR(500) DEFAULT '#',
    image_url VARCHAR(500),
    price_krw INT DEFAULT 29000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_code ON products(code);
CREATE INDEX idx_products_slot ON products(time_slot);

-- 6. 제품 클릭 및 CRM 로그 테이블 (product_click_logs)
DROP TABLE IF EXISTS product_click_logs CASCADE;
CREATE TABLE product_click_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    product_code VARCHAR(50) NOT NULL,
    time_slot VARCHAR(20) NOT NULL,
    clicked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. 제품 패키지 QR 온보딩 로그 테이블 (qr_onboarding_logs)
DROP TABLE IF EXISTS qr_onboarding_logs CASCADE;
CREATE TABLE qr_onboarding_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    qr_token VARCHAR(100) NOT NULL,
    product_code VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_converted BOOLEAN DEFAULT TRUE,
    scanned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_qr_logs_token ON qr_onboarding_logs(qr_token);

-- ====================================================================
-- 서카디언 4대 핵심 제품 초기 시드 데이터 (SEED DATA)
-- ====================================================================
INSERT INTO products (code, name, sub_title, description, time_slot, recommended_time, key_ingredients, purchase_url, price_krw)
VALUES
(
    'MORNING_RESET',
    'Morning Reset',
    '상쾌한 아침을 깨우는 전해질 & 비타민 C 부스터',
    '밤사이 호흡과 땀으로 손실된 수분을 급속 충전하고 신진대사를 깨워줍니다.',
    'MORNING',
    '08:00',
    '히말라야 핑크솔트, 전해질 4종, 비타민 C, 레몬 농축액',
    'https://circadian.kr/products/morning-reset',
    29000
),
(
    'DAY_FOCUS',
    'Day Focus',
    '나른한 오후의 활력 충전 & 집중력 부스터',
    '점심 식사 후 찾아오는 피로감을 덜어주고 오후 수분 밸런스를 맞춰줍니다.',
    'DAY',
    '13:00',
    '타우린, 비타민 B군, 과라나 추출물, L-카르니틴',
    'https://circadian.kr/products/day-focus',
    29000
),
(
    'EVENING_RELIEF',
    'Evening Relief',
    '퇴근 후 긴장 완화 & 전신 릴랙스 워터',
    '하루 동안 쌓인 신체 피로와 활성산소를 케어하며 저녁 수분을 보충합니다.',
    'EVENING',
    '18:00',
    'L-테아닌, 타트체리 농축액, 칼륨, 마그네슘',
    'https://circadian.kr/products/evening-relief',
    29000
),
(
    'NIGHT_CALM',
    'Night Calm',
    '숙면 리듬 형성 & 야간 탈수 방지 나이트 케어',
    '수면 중 목마름으로 깨지 않도록 부담 없이 체내 수분을 지켜줍니다.',
    'NIGHT',
    '22:00',
    '카모마일, 락티움, 글리신, 저분자 히알루론산',
    'https://circadian.kr/products/night-calm',
    29000
)
ON CONFLICT (code) DO NOTHING;
