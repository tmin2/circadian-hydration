# 💧 Circadian Hydration Platform

> **하루 1분 체크, Hydration Score™ 생성, 생체 리듬(Circadian Rhythm) 맞춤 수분 섭취 루틴 및 제품 큐레이션 D2C 플랫폼**

[![GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-0284c7?style=for-the-badge&logo=github)](https://tmin2.github.io/circadian-hydration/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=for-the-badge&logo=postgresql)](https://postgresql.org)

---

## 🌟 주요 기능 (MVP)

1. **30초 Morning Check (기상 후 1분 체크)**
   - 기상/수면 시간, 8단계 Armstrong 소변 색상 지표, 갈증/입마름 척도, 커피 및 운동 계획 점검.
2. **Hydration Score™ 엔진 (0~100점)**
   - 임상 지표와 체감 지표를 결합한 브랜드 고유의 수분 밸런스 지표 및 당일 맞춤 권장 수분량(L) 자동 산출.
3. **원터치 물 섭취 기록**
   - `+250ml (한 잔)`, `+500ml (텀블러)`, `+750ml`, `+1.0L (보틀)` 퀵 기록 및 100% 달성 시 축하 연출.
4. **24시간 서카디언 저니 (Circadian Journey)**
   - **08:00 Morning Reset**: 전해질 & 비타민 C 부스터
   - **13:00 Day Focus**: 오후 활력 충전 & 타우린/비타민 B군
   - **18:00 Evening Relief**: 긴장 완화 & L-테아닌/마그네슘
   - **22:00 Night Calm**: 숙면 유도 & 야간 탈수 예방 나이트 워터
5. **제품 패키지 QR 온보딩 & D2C CRM**
   - 언박싱 후 QR 스캔 시 맞춤 루틴 활성화 및 첫 루틴 할인 리워드.
   - 7일 취약 시간대 분석 리포트 및 25일차 자동 리필 알림.
6. **HealthKit / Samsung Health & 기온 연동**
   - 걸음 수(14,000보), 운동(60분), 폭염 기온(34℃) 반영 시 일일 권장량 동적 조정 (+1.6L 추가).

---

## 📱 실시간 웹 데모 (Mobile Web)

- **배포 주소**: **[https://tmin2.github.io/circadian-hydration/](https://tmin2.github.io/circadian-hydration/)**
- 스마트폰 및 PC 브라우저에서 모바일 화면으로 바로 체험할 수 있습니다.

---

## 🏗️ 프로젝트 구조

```text
circadian-hydration/
├── backend/                     # FastAPI 백엔드 서버
│   ├── app/
│   │   ├── api/                 # auth, morning_check, intake, dashboard, qr, admin
│   │   ├── core/                # DB 세션 및 환경 설정
│   │   ├── models/              # SQLAlchemy 2.0 ORM 엔티티
│   │   ├── schemas/             # Pydantic V2 DTO
│   │   ├── services/            # HydrationScoreEngine 코어 계산 로직
│   │   └── main.py              # 진입점 및 초기 제품 시딩
│   ├── migrations/              # PostgreSQL DDL (schema.sql)
│   ├── requirements.txt         # 백엔드 의존성
│   └── test_engine.py           # 계산 엔진 단위 테스트
├── frontend/                    # 프론트엔드 프로토타입
│   └── index.html
├── docs/                        # 상세 기획 및 전략 문서
│   └── CIRCADIAN_QR_STRATEGY.md
├── index.html                   # GitHub Pages 배포용 웹앱
└── README.md
```

---

## 🚀 로컬 실행 가이드

### 1. 프론트엔드 모바일웹 실행
```bash
python -m http.server 3000
```
브라우저에서 `http://localhost:3000` 접속

### 2. 백엔드 API 서버 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API 문서(Swagger UI): `http://localhost:8000/docs`
