"""
Dashboard (오늘 현황, 7일/30일 그래프, 서카디언 맞춤 제품 노출) API 라우터
"""

from datetime import date, datetime, timedelta
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.entities import MorningCheck, Product, User, WaterIntakeLog
from app.schemas.dto import DailyIntakeSummary, DashboardResponse, ProductResponse
from app.services.hydration_engine import HydrationScoreEngine

router = APIRouter(prefix="/dashboard", tags=["7. Dashboard & 서카디언 제품 추천"])


@router.get("/{user_id}", response_model=DashboardResponse, summary="대시보드 종합 데이터 조회")
async def get_dashboard_data(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> DashboardResponse:
    """
    오늘의 Hydration Score, 누적 물 섭취량 및 달성률, 현재 시간대에 알맞은
    서카디언 제품 카드와 지난 7일간의 히스토리 데이터를 한 번에 반환합니다.
    """
    today = date.today()

    # 1. 사용자 정보 확인
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 2. 오늘의 Morning Check 데이터 확인
    mc_stmt = select(MorningCheck).where(
        MorningCheck.user_id == user_id,
        MorningCheck.check_date == today,
    )
    mc_res = await db.execute(mc_stmt)
    today_check = mc_res.scalar_one_or_none()

    has_checked_morning = today_check is not None
    if today_check:
        hydration_score = today_check.hydration_score
        hydration_grade = today_check.hydration_grade
        recommended_water_ml = today_check.recommended_ml
    else:
        # 아침 체크 전 기본 디폴트 권장량 계산 (체중 기반)
        hydration_score = 0
        hydration_grade = "체크 필요"
        recommended_water_ml = HydrationScoreEngine.calculate_recommended_water(
            weight_kg=user.weight_kg,
            activity_level=user.activity_level,
        )

    # 3. 오늘 누적 물 섭취량 합산
    intake_sum_stmt = select(func.coalesce(func.sum(WaterIntakeLog.amount_ml), 0)).where(
        WaterIntakeLog.user_id == user_id,
        WaterIntakeLog.log_date == today,
    )
    intake_res = await db.execute(intake_sum_stmt)
    current_water_ml = intake_res.scalar_one()

    remaining_water_ml = max(0, recommended_water_ml - current_water_ml)
    achievement_rate = (
        round((current_water_ml / recommended_water_ml) * 100, 1)
        if recommended_water_ml > 0
        else 0.0
    )

    # 4. 현재 시각 기반 서카디언 단계 및 추천 제품 조회
    current_hour = datetime.now().hour
    slot, product_code, _ = HydrationScoreEngine.get_current_circadian_slot(current_hour)

    prod_stmt = select(Product).where(Product.code == product_code)
    prod_res = await db.execute(prod_stmt)
    product_entity = prod_res.scalar_one_or_none()
    recommended_product_dto: Optional[ProductResponse] = None

    if product_entity:
        recommended_product_dto = ProductResponse.model_validate(product_entity)
    else:
        # 기본 내장 서카디언 제품 정보 폴백
        default_products = {
            "MORNING_RESET": ProductResponse(
                id=uuid.uuid4(),
                code="MORNING_RESET",
                name="Morning Reset",
                sub_title="상쾌한 아침을 깨우는 전해질 & 비타민 C 부스터",
                description="밤사이 호흡과 땀으로 손실된 수분을 급속 충전하고 신진대사를 깨워줍니다.",
                time_slot="MORNING",
                recommended_time="08:00",
                key_ingredients="히말라야 핑크솔트, 전해질 4종, 비타민 C, 레몬 농축액",
                purchase_url="https://circadian.kr/products/morning-reset",
                image_url=None,
                price_krw=29000,
            ),
            "DAY_FOCUS": ProductResponse(
                id=uuid.uuid4(),
                code="DAY_FOCUS",
                name="Day Focus",
                sub_title="나른한 오후의 활력 충전 & 집중력 부스터",
                description="점심 식사 후 찾아오는 피로감을 덜어주고 오후 수분 밸런스를 맞춰줍니다.",
                time_slot="DAY",
                recommended_time="13:00",
                key_ingredients="타우린, 비타민 B군, 과라나 추출물, L-카르니틴",
                purchase_url="https://circadian.kr/products/day-focus",
                image_url=None,
                price_krw=29000,
            ),
            "EVENING_RELIEF": ProductResponse(
                id=uuid.uuid4(),
                code="EVENING_RELIEF",
                name="Evening Relief",
                sub_title="퇴근 후 긴장 완화 & 전신 릴랙스 워터",
                description="하루 동안 쌓인 신체 피로와 활성산소를 케어하며 저녁 수분을 보충합니다.",
                time_slot="EVENING",
                recommended_time="18:00",
                key_ingredients="L-테아닌, 타트체리 농축액, 칼륨, 마그네슘",
                purchase_url="https://circadian.kr/products/evening-relief",
                image_url=None,
                price_krw=29000,
            ),
            "NIGHT_CALM": ProductResponse(
                id=uuid.uuid4(),
                code="NIGHT_CALM",
                name="Night Calm",
                sub_title="숙면 리듬 형성 & 야간 탈수 방지 나이트 케어",
                description="수면 중 목마름으로 깨지 않도록 부담 없이 체내 수분을 지켜줍니다.",
                time_slot="NIGHT",
                recommended_time="22:00",
                key_ingredients="카모마일, 락티움, 글리신, 저분자 히알루론산",
                purchase_url="https://circadian.kr/products/night-calm",
                image_url=None,
                price_krw=29000,
            ),
        }
        recommended_product_dto = default_products.get(product_code)

    # 5. 최근 7일간의 히스토리 통계 집계
    weekly_history: List[DailyIntakeSummary] = []
    total_achievement_sum = 0.0

    for i in range(6, -1, -1):
        target_day = today - timedelta(days=i)
        target_day_str = target_day.strftime("%m/%d")

        # 해당 날짜 섭취량
        day_sum_stmt = select(func.coalesce(func.sum(WaterIntakeLog.amount_ml), 0)).where(
            WaterIntakeLog.user_id == user_id,
            WaterIntakeLog.log_date == target_day,
        )
        day_sum_res = await db.execute(day_sum_stmt)
        day_intake = day_sum_res.scalar_one()

        # 해당 날짜 스코어
        day_mc_stmt = select(MorningCheck).where(
            MorningCheck.user_id == user_id,
            MorningCheck.check_date == target_day,
        )
        day_mc_res = await db.execute(day_mc_stmt)
        past_mc = day_mc_res.scalar_one_or_none()

        rec_target = past_mc.recommended_ml if past_mc else recommended_water_ml
        rate = round((day_intake / rec_target) * 100, 1) if rec_target > 0 else 0.0
        total_achievement_sum += rate

        weekly_history.append(
            DailyIntakeSummary(
                date=target_day_str,
                total_intake_ml=day_intake,
                recommended_ml=rec_target,
                achievement_rate=min(100.0, rate),
                score=past_mc.hydration_score if past_mc else None,
            )
        )

    monthly_avg = round(total_achievement_sum / 7.0, 1)

    return DashboardResponse(
        today_date=today.strftime("%Y년 %m월 %d일"),
        has_checked_morning=has_checked_morning,
        hydration_score=hydration_score,
        hydration_grade=hydration_grade,
        recommended_water_ml=recommended_water_ml,
        current_water_ml=current_water_ml,
        remaining_water_ml=remaining_water_ml,
        achievement_rate=achievement_rate,
        current_circadian_slot=slot,
        recommended_product=recommended_product_dto,
        weekly_history=weekly_history,
        monthly_achievement_avg=monthly_avg,
    )
