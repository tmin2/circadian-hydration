"""
Circadian Hydration Engine - 수분 스코어 산출 및 서카디언 루틴 판별 서비스
"""

from datetime import datetime
from typing import Dict, Literal, Tuple


# 서카디언 리듬 시간 슬롯 타입
CircadianSlot = Literal["MORNING", "DAY", "EVENING", "NIGHT"]
HydrationGrade = Literal["매우 좋음", "좋음", "주의", "위험"]


class HydrationScoreEngine:
    """
    임상 및 생체 리듬 기반의 Hydration Score™ 계산 및 동적 수분 권장량을 도출하는 핵심 엔진
    """

    @staticmethod
    def calculate_score(
        urine_color: int,
        thirst_level: int,
        dry_mouth_level: int,
        sleep_hours: float,
        has_coffee_plan: bool,
        has_workout_plan: bool,
    ) -> Tuple[int, HydrationGrade]:
        """
        Morning Check 입력 지표를 바탕으로 100점 만점 점수 및 평가 등급 산출

        :param urine_color: 소변 색상 (1~8, Armstrong Urine Color Chart)
        :param thirst_level: 체감 갈증 척도 (1~5)
        :param dry_mouth_level: 체감 입마름 척도 (1~5)
        :param sleep_hours: 총 수면 시간 (h)
        :param has_coffee_plan: 카페인 섭취 계획
        :param has_workout_plan: 운동 계획
        :return: (Hydration Score 정수, 등급 라벨)
        """
        score: float = 0.0

        # 1. 소변 색상 점수 (최대 40점)
        # Armstrong 의학 차트 기준: 1~3단계는 충분한 수분, 4~5단계는 가벼운 탈수, 6~8단계는 심한 탈수
        if urine_color <= 2:
            score += 40.0
        elif urine_color == 3:
            score += 35.0
        elif urine_color in (4, 5):
            score += 24.0
        elif urine_color in (6, 7):
            score += 12.0
        else:
            score += 5.0

        # 2. 체감 갈증 및 입마름 척도 점수 (최대 30점)
        # 갈증(1~5) + 입마름(1~5) = 2~10. 낮을수록 수분 상태 우수
        discomfort_sum = thirst_level + dry_mouth_level
        # 불편도 합계 2점(최상) -> 30점, 10점(최악) -> 0점
        score += max(0.0, (10 - discomfort_sum) * 3.75)

        # 3. 서카디언 수면 시간 충실도 점수 (최대 20점)
        # 성인 권장 수면 7.0 ~ 8.5시간에 최적 가중치 부여
        if 7.0 <= sleep_hours <= 8.5:
            score += 20.0
        elif 6.0 <= sleep_hours < 7.0 or 8.5 < sleep_hours <= 9.5:
            score += 15.0
        else:
            score += 10.0

        # 4. 당일 생체 부하 대비 점수 (최대 10점)
        # 카페인(이뇨) 및 운동(땀 배출) 계획 시 사전 주의 가중치
        prep_score = 10.0
        if has_coffee_plan:
            prep_score -= 3.0
        if has_workout_plan:
            prep_score -= 2.0
        score += max(0.0, prep_score)

        final_score = int(round(score))
        final_score = max(0, min(100, final_score))

        # 등급 판정
        if final_score >= 85:
            grade: HydrationGrade = "매우 좋음"
        elif final_score >= 70:
            grade: HydrationGrade = "좋음"
        elif final_score >= 50:
            grade: HydrationGrade = "주의"
        else:
            grade: HydrationGrade = "위험"

        return final_score, grade

    @staticmethod
    def calculate_recommended_water(
        weight_kg: float,
        activity_level: str = "moderate",
        has_coffee_plan: bool = False,
        has_workout_plan: bool = False,
        steps: int = 0,
        workout_minutes: int = 0,
        temperature_c: float = 23.0,
    ) -> int:
        """
        사용자 체중, 활동량, 기온, 헬스 데이터(걸음/운동)를 결합한 일일 권장 수분 섭취량(ml) 계산

        :param weight_kg: 체중(kg)
        :param activity_level: 기본 활동량 수준
        :param has_coffee_plan: 커피 예정 여부
        :param has_workout_plan: 운동 예정 여부
        :param steps: HealthKit/Samsung Health 동기화 걸음 수
        :param workout_minutes: 실제 측정 운동 시간 (분)
        :param temperature_c: 현재/예보 기온 (℃)
        :return: 권장 수분량 (ml, 50ml 단위 절상)
        """
        # 1. 기본 기초 수분량: 체중(kg) * 33ml
        base_ml = weight_kg * 33.0

        # 2. 기본 활동량 등급별 기본 보정
        activity_multipliers = {
            "sedentary": 0.0,
            "light": 100.0,
            "moderate": 200.0,
            "active": 400.0,
            "very_active": 600.0,
        }
        activity_extra = activity_multipliers.get(activity_level, 200.0)

        # 3. 걸음 수(Apple/Samsung Health) 보정: 10,000보 초과 시 1,000보당 50ml 추가
        steps_extra = max(0, (steps - 10000) // 1000) * 50.0

        # 4. 운동 시간 보정: 30분당 350ml (센서 연동이 없으면 모닝 체크의 운동 계획 기준 45분 가정)
        effective_workout_min = workout_minutes if workout_minutes > 0 else (45 if has_workout_plan else 0)
        workout_extra = (effective_workout_min / 30.0) * 350.0

        # 5. 외부 기온 보정
        temp_extra = 0.0
        if temperature_c >= 33.0:
            temp_extra = 400.0  # 폭염 대비
        elif temperature_c >= 28.0:
            temp_extra = 200.0  # 여름철 고온 대비

        # 6. 카페인 보정 (1잔당 150ml 추가 권장)
        coffee_extra = 150.0 if has_coffee_plan else 0.0

        total_ml = base_ml + activity_extra + steps_extra + workout_extra + temp_extra + coffee_extra

        # 50ml 단위로 깔끔하게 정돈 (최소 1,500ml 보장)
        final_ml = max(1500, int(round(total_ml / 50.0) * 50))
        return final_ml

    @staticmethod
    def get_current_circadian_slot(current_hour: int) -> Tuple[CircadianSlot, str, str]:
        """
        현재 시각(24시간제)에 따라 해당하는 서카디언 단계 및 추천 제품 코드 반환

        :param current_hour: 0~23 시각
        :return: (슬롯, 추천 제품 코드, 알림 및 루틴 타이틀)
        """
        if 5 <= current_hour < 11:
            return "MORNING", "MORNING_RESET", "Morning Reset (밤사이 손실된 수분과 활력 충전)"
        elif 11 <= current_hour < 17:
            return "DAY", "DAY_FOCUS", "Day Focus (오후 집중력 강화 & 전해질 밸런스)"
        elif 17 <= current_hour < 21:
            return "EVENING", "EVENING_RELIEF", "Evening Relief (일과 후 긴장 완화 & 수분 유지)"
        else:
            return "NIGHT", "NIGHT_CALM", "Night Calm (숙면을 위한 릴랙스 & 야간 탈수 예방)"
