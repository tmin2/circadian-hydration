"""
Morning Check (매일 아침 30초 체크) API 라우터
"""

from datetime import date, datetime, time
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.entities import MorningCheck, User
from app.schemas.dto import MorningCheckCreate, MorningCheckResponse
from app.services.hydration_engine import HydrationScoreEngine

router = APIRouter(prefix="/morning-check", tags=["2. Morning Check (아침 30초 체크)"])


@router.post("/{user_id}", response_model=MorningCheckResponse, summary="아침 30초 체크 제출 및 스코어 산출")
async def submit_morning_check(
    user_id: uuid.UUID,
    check_in: MorningCheckCreate,
    db: AsyncSession = Depends(get_db_session),
) -> MorningCheckResponse:
    """
    기상 직후 약 30초간 6가지 항목(기상/수면, 갈증, 입마름, 소변색, 커피, 운동)을 입력받아
    즉시 Hydration Score와 오늘 맞춤 권장 수분량(L)을 산출하고 저장합니다.
    """
    # 1. 사용자 프로필 조회 (신체 데이터 반영 목적)
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 정보를 찾을 수 없습니다.",
        )

    # 2. Hydration Score 및 등급 산출
    score, grade = HydrationScoreEngine.calculate_score(
        urine_color=check_in.urine_color,
        thirst_level=check_in.thirst_level,
        dry_mouth_level=check_in.dry_mouth_level,
        sleep_hours=check_in.sleep_hours,
        has_coffee_plan=check_in.has_coffee_plan,
        has_workout_plan=check_in.has_workout_plan,
    )

    # 3. 오늘 권장 수분 섭취량(ml) 자동 계산
    recommended_ml = HydrationScoreEngine.calculate_recommended_water(
        weight_kg=user.weight_kg,
        activity_level=user.activity_level,
        has_coffee_plan=check_in.has_coffee_plan,
        has_workout_plan=check_in.has_workout_plan,
    )

    # 기상 시간 파싱 (HH:MM -> time 객체)
    hour, minute = map(int, check_in.wake_time.split(":"))
    wake_t = time(hour=hour, minute=minute)

    # 4. 당일 체크 여부 확인 (하루 1회 갱신 또는 신규 생성)
    today = date.today()
    check_stmt = select(MorningCheck).where(
        MorningCheck.user_id == user_id,
        MorningCheck.check_date == today,
    )
    check_res = await db.execute(check_stmt)
    record = check_res.scalar_one_or_none()

    if record:
        # 기존 기록 업데이트
        record.wake_time = wake_t
        record.sleep_hours = check_in.sleep_hours
        record.thirst_level = check_in.thirst_level
        record.dry_mouth_level = check_in.dry_mouth_level
        record.urine_color = check_in.urine_color
        record.has_coffee_plan = check_in.has_coffee_plan
        record.has_workout_plan = check_in.has_workout_plan
        record.hydration_score = score
        record.hydration_grade = grade
        record.recommended_ml = recommended_ml
    else:
        # 신규 체크 레코드 생성
        record = MorningCheck(
            user_id=user_id,
            check_date=today,
            wake_time=wake_t,
            sleep_hours=check_in.sleep_hours,
            thirst_level=check_in.thirst_level,
            dry_mouth_level=check_in.dry_mouth_level,
            urine_color=check_in.urine_color,
            has_coffee_plan=check_in.has_coffee_plan,
            has_workout_plan=check_in.has_workout_plan,
            hydration_score=score,
            hydration_grade=grade,
            recommended_ml=recommended_ml,
        )
        db.add(record)

    await db.commit()
    await db.refresh(record)

    return MorningCheckResponse.model_validate(record)


@router.get("/today/{user_id}", response_model=MorningCheckResponse, summary="오늘 아침 체크 결과 조회")
async def get_today_morning_check(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> MorningCheckResponse:
    """오늘 작성된 아침 체크 결과 및 점수 조회"""
    today = date.today()
    stmt = select(MorningCheck).where(
        MorningCheck.user_id == user_id,
        MorningCheck.check_date == today,
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="오늘의 Morning Check 기록이 없습니다.",
        )

    return MorningCheckResponse.model_validate(record)
