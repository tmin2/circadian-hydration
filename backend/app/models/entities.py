"""
Circadian Hydration Platform - SQLAlchemy ORM 엔티티 모델 정의
"""

import uuid
from datetime import date, datetime, time
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    """사용자 계정 및 생체 프로필 엔티티"""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(
        String(50), default="email", comment="email | kakao | naver | google"
    )
    provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str] = mapped_column(String(100), default="수분탐험가")

    # 신체 및 활동량 프로필 (수분 권장량 산출에 활용)
    gender: Mapped[str] = mapped_column(String(10), default="unspecified")  # male, female, other
    age: Mapped[int] = mapped_column(Integer, default=30)
    height_cm: Mapped[float] = mapped_column(Float, default=170.0)
    weight_kg: Mapped[float] = mapped_column(Float, default=65.0)
    activity_level: Mapped[str] = mapped_column(
        String(50), default="moderate", comment="sedentary | light | moderate | active | very_active"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 연관 관계
    morning_checks: Mapped[List["MorningCheck"]] = relationship(
        "MorningCheck", back_populates="user", cascade="all, delete-orphan"
    )
    water_logs: Mapped[List["WaterIntakeLog"]] = relationship(
        "WaterIntakeLog", back_populates="user", cascade="all, delete-orphan"
    )


class MorningCheck(Base):
    """매일 기상 후 30초 체크 기록 엔티티"""
    __tablename__ = "morning_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    check_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    wake_time: Mapped[time] = mapped_column(Time, comment="기상 시간 (HH:MM)")
    sleep_hours: Mapped[float] = mapped_column(Float, comment="수면 시간 (시간 단위)")

    # 자가 점검 척도
    thirst_level: Mapped[int] = mapped_column(Integer, comment="갈증 정도 (1~5)")
    dry_mouth_level: Mapped[int] = mapped_column(Integer, comment="입마름 정도 (1~5)")
    urine_color: Mapped[int] = mapped_column(Integer, comment="소변 색상 단계 (1~8)")
    has_coffee_plan: Mapped[bool] = mapped_column(Boolean, default=False, comment="커피 예정 여부")
    has_workout_plan: Mapped[bool] = mapped_column(Boolean, default=False, comment="운동 예정 여부")

    # 계산 엔진 산출 결과
    hydration_score: Mapped[int] = mapped_column(Integer, comment="Hydration Score (0~100)")
    hydration_grade: Mapped[str] = mapped_column(String(20), comment="매우 좋음 | 좋음 | 주의 | 위험")
    recommended_ml: Mapped[int] = mapped_column(Integer, comment="오늘 권장 수분 섭취량 (ml)")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 연관 관계
    user: Mapped["User"] = relationship("User", back_populates="morning_checks")


class WaterIntakeLog(Base):
    """물 섭취 기록 엔티티 (+250ml, +500ml 등 원터치)"""
    __tablename__ = "water_intake_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    amount_ml: Mapped[int] = mapped_column(Integer, comment="섭취량 (ml)")
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    log_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)

    # 연관 관계
    user: Mapped["User"] = relationship("User", back_populates="water_logs")


class Product(Base):
    """서카디언 리듬 제품 정보 엔티티"""
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, comment="MORNING_RESET | DAY_FOCUS | EVENING_RELIEF | NIGHT_CALM"
    )
    name: Mapped[str] = mapped_column(String(100), comment="제품명 (예: Morning Reset)")
    sub_title: Mapped[str] = mapped_column(String(200), comment="제품 한 줄 소개")
    description: Mapped[str] = mapped_column(String(1000), comment="상세 설명 및 효능")
    time_slot: Mapped[str] = mapped_column(
        String(20), comment="서카디언 슬롯 (MORNING | DAY | EVENING | NIGHT)"
    )
    recommended_time: Mapped[str] = mapped_column(String(20), default="08:00")
    key_ingredients: Mapped[str] = mapped_column(String(255), comment="핵심 성분 (예: 전해질, 타우린 등)")
    purchase_url: Mapped[str] = mapped_column(String(500), default="#")
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    price_krw: Mapped[int] = mapped_column(Integer, default=29000)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProductClickLog(Base):
    """제품 클릭 및 CRM 통계 트래킹 엔티티"""
    __tablename__ = "product_click_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    product_code: Mapped[str] = mapped_column(String(50), index=True)
    time_slot: Mapped[str] = mapped_column(String(20))
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QROnboardingLog(Base):
    """제품 패키지 QR 스캔 트래킹 엔티티"""
    __tablename__ = "qr_onboarding_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    qr_token: Mapped[str] = mapped_column(String(100), index=True)
    product_code: Mapped[str] = mapped_column(String(50))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_converted: Mapped[bool] = mapped_column(Boolean, default=False, comment="루틴 시작 전환 여부")
