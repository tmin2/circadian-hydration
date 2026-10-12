"""
물 섭취 기록 API 라우터 (+250ml, +500ml, +750ml, +1L 등 원터치)
"""

from datetime import date
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.entities import WaterIntakeLog
from app.schemas.dto import WaterIntakeCreate, WaterIntakeResponse

router = APIRouter(prefix="/intake", tags=["4. 물 섭취 기록 (원터치)"])


@router.post("/{user_id}", response_model=WaterIntakeResponse, summary="원터치 물 섭취 기록 추가")
async def add_water_intake(
    user_id: uuid.UUID,
    intake_data: WaterIntakeCreate,
    db: AsyncSession = Depends(get_db_session),
) -> WaterIntakeResponse:
    """
    버튼 클릭(+250ml, +500ml, +750ml, +1000ml) 시 실시간 수분 섭취량을 누적 저장합니다.
    """
    log = WaterIntakeLog(
        user_id=user_id,
        amount_ml=intake_data.amount_ml,
        log_date=date.today(),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return WaterIntakeResponse.model_validate(log)


@router.get("/today/{user_id}", response_model=List[WaterIntakeResponse], summary="오늘 섭취한 물 상세 로그 목록")
async def get_today_intake_logs(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> List[WaterIntakeResponse]:
    """오늘 기록된 물 섭취 상세 타임라인 목록을 최신순으로 조회합니다."""
    today = date.today()
    stmt = (
        select(WaterIntakeLog)
        .where(
            WaterIntakeLog.user_id == user_id,
            WaterIntakeLog.log_date == today,
        )
        .order_by(desc(WaterIntakeLog.logged_at))
    )
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [WaterIntakeResponse.model_validate(log) for log in logs]


@router.delete("/latest/{user_id}", summary="가장 최근 섭취 기록 취소 (실수 수정용)")
async def delete_latest_intake(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """실수로 잘못 누른 경우 직전에 입력한 물 섭취 기록을 1건 취소합니다."""
    today = date.today()
    stmt = (
        select(WaterIntakeLog)
        .where(
            WaterIntakeLog.user_id == user_id,
            WaterIntakeLog.log_date == today,
        )
        .order_by(desc(WaterIntakeLog.logged_at))
        .limit(1)
    )
    res = await db.execute(stmt)
    latest_log = res.scalar_one_or_none()

    if not latest_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="취소할 수분 기록이 없습니다.",
        )

    amount = latest_log.amount_ml
    await db.delete(latest_log)
    await db.commit()

    return {"message": f"최근 기록된 {amount}ml 수분 섭취가 취소되었습니다."}
