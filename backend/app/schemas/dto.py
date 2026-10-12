"""
Circadian Hydration Platform - Pydantic DTO 스키마 정의 모듈
"""

from datetime import date, datetime, time
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==========================================
# 1. 사용자 및 인증 관련 스키마
# ==========================================
class UserProfileBase(BaseModel):
    """사용자 신체 및 생활 프로필 기본 스키마"""
    nickname: str = Field(default="수분탐험가", description="사용자 닉네임")
    gender: str = Field(default="female", description="성별 (male | female | other)")
    age: int = Field(default=28, ge=1, le=120, description="나이")
    height_cm: float = Field(default=165.0, ge=50.0, le=250.0, description="신장 (cm)")
    weight_kg: float = Field(default=55.0, ge=30.0, le=300.0, description="체중 (kg)")
    activity_level: str = Field(
        default="moderate",
        description="활동량 수준 (sedentary: 좌식, light: 가벼움, moderate: 보통, active: 활발, very_active: 매우 활발)",
    )


class UserRegisterRequest(UserProfileBase):
    """이메일/소셜 회원가입 요청"""
    email: EmailStr = Field(description="이메일 주소")
    password: Optional[str] = Field(default=None, description="비밀번호 (소셜 로그인 시 생략 가능)")
    provider: str = Field(default="email", description="가입 제공자 (kakao | naver | google | email)")
    provider_id: Optional[str] = Field(default=None, description="소셜 로그인 식별자")


class UserLoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr = Field(description="이메일")
    password: Optional[str] = Field(default=None, description="비밀번호")
    provider: str = Field(default="email", description="가입 제공자")


class TokenResponse(BaseModel):
    """인증 토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    nickname: str
    email: str


class UserResponse(UserProfileBase):
    """사용자 상세 조회 응답"""
    id: UUID
    email: str
    provider: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Morning Check (30초 아침 체크) 스키마
# ==========================================
class MorningCheckCreate(BaseModel):
    """아침 30초 체크 입력 스키마"""
    wake_time: str = Field(
        default="07:30", description="기상 시간 (HH:MM 포맷)", pattern=r"^\d{2}:\d{2}$"
    )
    sleep_hours: float = Field(
        default=7.5, ge=1.0, le=24.0, description="수면 시간 (시간 단위, 예: 7.5)"
    )
    thirst_level: int = Field(
        default=2, ge=1, le=5, description="갈증 정도 (1: 없음 ~ 5: 극심함)"
    )
    dry_mouth_level: int = Field(
        default=2, ge=1, le=5, description="입마름 정도 (1: 없음 ~ 5: 극심함)"
    )
    urine_color: int = Field(
        default=3, ge=1, le=8, description="소변 색상 단계 (1: 투명 ~ 8: 짙은 갈색)"
    )
    has_coffee_plan: bool = Field(
        default=False, description="오늘 커피/카페인 섭취 계획 여부"
    )
    has_workout_plan: bool = Field(
        default=False, description="오늘 30분 이상 운동 예정 여부"
    )


class MorningCheckResponse(BaseModel):
    """아침 체크 완료 및 계산 결과 응답"""
    id: UUID
    user_id: UUID
    check_date: date
    wake_time: time
    sleep_hours: float
    thirst_level: int
    dry_mouth_level: int
    urine_color: int
    has_coffee_plan: bool
    has_workout_plan: bool
    hydration_score: int = Field(description="Hydration Score (0~100점)")
    hydration_grade: str = Field(description="수분 등급 (매우 좋음 | 좋음 | 주의 | 위험)")
    recommended_ml: int = Field(description="오늘 권장 총 수분 섭취량 (ml)")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. 물 섭취 기록 스키마
# ==========================================
class WaterIntakeCreate(BaseModel):
    """원터치 수분 섭취 기록 추가"""
    amount_ml: int = Field(
        ...,
        description="섭취량 (ml). 권장 버튼: 250, 500, 750, 1000",
        ge=50,
        le=2000,
    )


class WaterIntakeResponse(BaseModel):
    """물 섭취 기록 단건 응답"""
    id: UUID
    user_id: UUID
    amount_ml: int
    logged_at: datetime
    log_date: date

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. 서카디언 제품 스키마
# ==========================================
class ProductResponse(BaseModel):
    """서카디언 추천 제품 정보"""
    id: UUID
    code: str
    name: str
    sub_title: str
    description: str
    time_slot: str  # MORNING, DAY, EVENING, NIGHT
    recommended_time: str
    key_ingredients: str
    purchase_url: str
    image_url: Optional[str] = None
    price_krw: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. Dashboard 및 통계 응답 스키마
# ==========================================
class DailyIntakeSummary(BaseModel):
    """특정 날짜의 수분 섭취 요약"""
    date: str
    total_intake_ml: int
    recommended_ml: int
    achievement_rate: float
    score: Optional[int] = None


class DashboardResponse(BaseModel):
    """대시보드 메인 화면 통합 데이터 응답"""
    today_date: str
    has_checked_morning: bool
    hydration_score: int
    hydration_grade: str
    recommended_water_ml: int
    current_water_ml: int
    remaining_water_ml: int
    achievement_rate: float  # 달성률 (0.0 ~ 100.0%)

    # 현재 서카디언 시간대 & 추천 제품
    current_circadian_slot: str  # MORNING | DAY | EVENING | NIGHT
    recommended_product: Optional[ProductResponse] = None

    # 주간 및 월간 통계 그래프 데이터
    weekly_history: List[DailyIntakeSummary]
    monthly_achievement_avg: float


# ==========================================
# 6. QR 온보딩 및 CRM 트래킹 스키마
# ==========================================
class QRScanRequest(BaseModel):
    """제품 패키지 QR 스캔 요청"""
    qr_token: str = Field(..., description="QR 코드 내 포함된 고유 토큰")
    product_code: str = Field(..., description="스캔된 제품 코드 (예: MORNING_RESET)")


class QRScanResponse(BaseModel):
    """QR 스캔 처리 결과"""
    is_valid: bool
    product: ProductResponse
    routine_message: str
    discount_benefit: str
