"""
관리자 페이지 API 라우터 (회원관리, 점수통계, 제품클릭, 리텐션, 푸시 발송)
"""

from typing import Any, Dict, List
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.entities import MorningCheck, ProductClickLog, QROnboardingLog, User

router = APIRouter(prefix="/admin", tags=["관리자 페이지"])


@router.get("/summary", summary="관리자 대시보드 종합 지표")
async def get_admin_summary(
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    회원수, 평균 Hydration Score, 제품 클릭수, QR 온보딩 전환율 통계를 조회합니다.
    """
    # 1. 총 회원 수
    user_count_stmt = select(func.count(User.id))
    user_count_res = await db.execute(user_count_stmt)
    total_users = user_count_res.scalar_one()

    # 2. 전체 Morning Check 평균 스코어
    score_avg_stmt = select(func.avg(MorningCheck.hydration_score))
    score_avg_res = await db.execute(score_avg_stmt)
    avg_score = score_avg_res.scalar_one() or 0.0

    # 3. QR 스캔 및 전환 건수
    qr_count_stmt = select(func.count(QROnboardingLog.id))
    qr_res = await db.execute(qr_count_stmt)
    total_qr_scans = qr_res.scalar_one()

    # 4. 제품 클릭 수
    click_count_stmt = select(func.count(ProductClickLog.id))
    click_res = await db.execute(click_count_stmt)
    total_clicks = click_res.scalar_one()

    return {
        "total_members": total_users,
        "average_hydration_score": round(float(avg_score), 1),
        "qr_scans": total_qr_scans,
        "product_clicks": total_clicks,
        "retention_rate_7d": 68.4,  # MVP 샘플 통계
        "circadian_completion_rate": 74.2,
    }


@router.post("/push/simulate", summary="서카디언 정시 Push 알림 발송 시뮬레이션")
async def simulate_push_notification(time_slot: str) -> Dict[str, Any]:
    """
    08:00, 13:00, 18:00, 22:00 정시 푸시 알림 발송을 시뮬레이션합니다.
    """
    messages = {
        "08:00": {
            "title": "[Morning Reset] 기상 후 1분 체크 알림",
            "body": "밤새 손실된 수분을 깨워주세요! 오늘 아침 Hydration Score를 확인하고 Morning Reset을 시작해보세요.",
            "product": "Morning Reset",
        },
        "13:00": {
            "title": "[Day Focus] 오후 활력 충전 시간",
            "body": "나른한 오후, 시원한 물 500ml와 Day Focus로 집중력을 높여보세요!",
            "product": "Day Focus",
        },
        "18:00": {
            "title": "[Evening Relief] 하루의 피로를 비우는 시간",
            "body": "퇴근 후 가벼운 스트레칭과 함께 Evening Relief로 체내 밸런스를 맞춰보세요.",
            "product": "Evening Relief",
        },
        "22:00": {
            "title": "[Night Calm] 편안한 밤을 위한 수분 루틴",
            "body": "숙면 중 갈증을 예방하는 Night Calm 한 잔으로 하루를 마무리하세요.",
            "product": "Night Calm",
        },
    }

    target = messages.get(
        time_slot,
        {
            "title": "[Circadian] 수분 루틴 알림",
            "body": "지금은 건강한 수분을 보충할 시간입니다.",
            "product": "Default",
        },
    )

    return {
        "status": "success",
        "time_slot": time_slot,
        "notification_payload": target,
        "sent_count": 1284,
    }
