"""
Circadian Hydration Platform - FastAPI 애플리케이션 진입점 (main.py)
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.intake import router as intake_router
from app.api.morning_check import router as morning_check_router
from app.api.qr import router as qr_router
from app.core.config import settings
from app.core.database import async_session_maker, engine
from app.models.entities import Base, Product


async def seed_initial_products() -> None:
    """초기 서카디언 리듬 4종 제품 데이터 자동 등록"""
    async with async_session_maker() as session:
        result = await session.execute(select(Product))
        existing = result.scalars().first()
        if existing:
            return  # 이미 시딩됨

        initial_products = [
            Product(
                id=uuid.uuid4(),
                code="MORNING_RESET",
                name="Morning Reset",
                sub_title="상쾌한 아침을 깨우는 전해질 & 비타민 C 부스터",
                description="밤사이 호흡과 땀으로 손실된 수분을 급속 충전하고 신진대사를 깨워줍니다.",
                time_slot="MORNING",
                recommended_time="08:00",
                key_ingredients="히말라야 핑크솔트, 전해질 4종, 비타민 C, 레몬 농축액",
                purchase_url="https://circadian.kr/products/morning-reset",
                price_krw=29000,
            ),
            Product(
                id=uuid.uuid4(),
                code="DAY_FOCUS",
                name="Day Focus",
                sub_title="나른한 오후의 활력 충전 & 집중력 부스터",
                description="점심 식사 후 찾아오는 피로감을 덜어주고 오후 수분 밸런스를 맞춰줍니다.",
                time_slot="DAY",
                recommended_time="13:00",
                key_ingredients="타우린, 비타민 B군, 과라나 추출물, L-카르니틴",
                purchase_url="https://circadian.kr/products/day-focus",
                price_krw=29000,
            ),
            Product(
                id=uuid.uuid4(),
                code="EVENING_RELIEF",
                name="Evening Relief",
                sub_title="퇴근 후 긴장 완화 & 전신 릴랙스 워터",
                description="하루 동안 쌓인 신체 피로와 활성산소를 케어하며 저녁 수분을 보충합니다.",
                time_slot="EVENING",
                recommended_time="18:00",
                key_ingredients="L-테아닌, 타트체리 농축액, 칼륨, 마그네슘",
                purchase_url="https://circadian.kr/products/evening-relief",
                price_krw=29000,
            ),
            Product(
                id=uuid.uuid4(),
                code="NIGHT_CALM",
                name="Night Calm",
                sub_title="숙면 리듬 형성 & 야간 탈수 방지 나이트 케어",
                description="수면 중 목마름으로 깨지 않도록 부담 없이 체내 수분을 지켜줍니다.",
                time_slot="NIGHT",
                recommended_time="22:00",
                key_ingredients="카모마일, 락티움, 글리신, 저분자 히알루론산",
                purchase_url="https://circadian.kr/products/night-calm",
                price_krw=29000,
            ),
        ]

        session.add_all(initial_products)
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """애플리케이션 생명주기 관리자: 시작 시 DB 테이블 확인 및 시딩"""
    try:
        # DB 테이블 자동 생성 (개발/MVP 편의성)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # 초기 제품 시딩
        await seed_initial_products()
    except Exception as e:
        print(f"[Warning] DB Init / Seed skipped or failed (check DB connection): {e}")

    yield

    # 종료 시 엔진 리소스 해제
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="하루 1분 체크로 생체 리듬(Circadian)에 맞는 수분 섭취와 제품을 추천하는 헬스케어 D2C 플랫폼 API",
    lifespan=lifespan,
)

# CORS 미들웨어 등록
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(morning_check_router, prefix=settings.API_V1_PREFIX)
app.include_router(intake_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(qr_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["상태 확인"])
async def root_health_check():
    """서버 상태 헬스체크"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
    }
