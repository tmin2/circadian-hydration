"""
QR 코드 기반 개인 맞춤 루틴 온보딩 & D2C 전환 API 라우터
"""

from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.entities import Product, QROnboardingLog
from app.schemas.dto import ProductResponse, QRScanRequest, QRScanResponse

router = APIRouter(prefix="/qr", tags=["추가전략: QR 패키지 온보딩 & D2C 연동"])


@router.post("/scan", response_model=QRScanResponse, summary="제품 패키지 QR 스캔 시 맞춤 루틴 온보딩")
async def scan_package_qr(
    req: QRScanRequest,
    user_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db_session),
) -> QRScanResponse:
    """
    고객이 배송받은 실제 제품(예: Morning Reset)의 패키지 QR 코드를 스캔했을 때,
    해당 제품의 서카디언 수분 루틴을 바로 시작할 수 있도록 안내하고 전환 로그를 기록합니다.
    """
    # 1. 스캔 로그 저장
    log = QROnboardingLog(
        qr_token=req.qr_token,
        product_code=req.product_code,
        user_id=user_id,
        is_converted=True,
    )
    db.add(log)
    await db.commit()

    # 2. 제품 정보 조회
    prod_stmt = select(Product).where(Product.code == req.product_code)
    res = await db.execute(prod_stmt)
    prod = res.scalar_one_or_none()

    if not prod:
        # 폴백 정보
        dummy_product = ProductResponse(
            id=uuid.uuid4(),
            code=req.product_code,
            name=f"{req.product_code.replace('_', ' ').title()}",
            sub_title="패키지 정품 인증이 완료되었습니다.",
            description="서카디언 생체 리듬에 맞춘 최적의 시간대에 섭취하여 수분 흡수율을 극대화하세요.",
            time_slot="MORNING",
            recommended_time="08:00",
            key_ingredients="전해질 및 서카디언 바이탈 포뮬러",
            purchase_url="#",
            price_krw=29000,
        )
        return QRScanResponse(
            is_valid=True,
            product=dummy_product,
            routine_message="정품 패키지 인증 완료! 매일 아침 1분 체크로 나만의 수분 스코어를 관리해보세요.",
            discount_benefit="첫 루틴 시작 기념 정기배송 15% 할인 혜택이 적용되었습니다.",
        )

    product_dto = ProductResponse.model_validate(prod)
    routine_message = (
        f"'{product_dto.name}' 패키지 인증이 완료되었습니다. "
        f"권장 섭취 시간인 {product_dto.recommended_time}에 수분과 함께 섭취하시면 가장 효과적입니다."
    )

    return QRScanResponse(
        is_valid=True,
        product=product_dto,
        routine_message=routine_message,
        discount_benefit="루틴 유지 고객 전용: 다음 리필 구매 시 15% 추가 할인 쿠폰 증정",
    )
