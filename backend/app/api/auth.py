"""
인증 및 사용자 프로필 관리 API 라우터
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.models.entities import User
from app.schemas.dto import (
    TokenResponse,
    UserLoginRequest,
    UserProfileBase,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["1. 사용자 & 인증"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(user_id: uuid.UUID, email: str) -> str:
    """JWT 토큰 생성 헬퍼 함수"""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post("/register", response_model=TokenResponse, summary="회원가입 (이메일/소셜 공용)")
async def register_user(
    req: UserRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    카카오/네이버/구글 또는 이메일을 통한 신규 회원가입 및 프로필 초기 등록
    """
    # 중복 이메일 체크
    stmt = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일 주소입니다.",
        )

    hashed_pw = pwd_context.hash(req.password) if req.password else None

    new_user = User(
        email=req.email,
        hashed_password=hashed_pw,
        provider=req.provider,
        provider_id=req.provider_id,
        nickname=req.nickname,
        gender=req.gender,
        age=req.age,
        height_cm=req.height_cm,
        weight_kg=req.weight_kg,
        activity_level=req.activity_level,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token(new_user.id, new_user.email)
    return TokenResponse(
        access_token=token,
        user_id=new_user.id,
        nickname=new_user.nickname,
        email=new_user.email,
    )


@router.post("/login", response_model=TokenResponse, summary="로그인")
async def login_user(
    req: UserLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    기존 사용자 로그인 및 토큰 발급 (소셜 로그인 테스트 지원)
    """
    stmt = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # 데모 및 빠른 테스트 편의를 위해 없는 경우 자동 등록 지원
        user = User(
            email=req.email,
            nickname=req.email.split("@")[0],
            provider=req.provider,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif req.password and user.hashed_password:
        if not pwd_context.verify(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비밀번호가 일치하지 않습니다.",
            )

    token = create_access_token(user.id, user.email)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        nickname=user.nickname,
        email=user.email,
    )


@router.get("/profile/{user_id}", response_model=UserResponse, summary="프로필 정보 조회")
async def get_profile(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """사용자의 기본 정보 및 신체/활동량 프로필 조회"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return UserResponse.model_validate(user)
