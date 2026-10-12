"""
Circadian Hydration Engine 단위 검증 테스트 스크립트
"""

from app.services.hydration_engine import HydrationScoreEngine


def test_hydration_engine_scenarios():
    print("=== Circadian Hydration Engine 테스트 시작 ===")

    # 시나리오 1: 기상 후 최상 상태 (수면 8시간, 갈증 1, 입마름 1, 소변 1단계, 운동X, 커피X)
    score1, grade1 = HydrationScoreEngine.calculate_score(
        urine_color=1,
        thirst_level=1,
        dry_mouth_level=1,
        sleep_hours=8.0,
        has_coffee_plan=False,
        has_workout_plan=False,
    )
    print(f"[시나리오 1 - 최적 상태] 점수: {score1}점, 등급: {grade1}")
    assert score1 >= 90, "최적 상태는 90점 이상이어야 합니다."
    assert grade1 == "매우 좋음"

    # 시나리오 2: 탈수 의심 상태 (수면 5시간, 갈증 4, 입마름 4, 소변 6단계, 운동O, 커피O)
    score2, grade2 = HydrationScoreEngine.calculate_score(
        urine_color=6,
        thirst_level=4,
        dry_mouth_level=4,
        sleep_hours=5.0,
        has_coffee_plan=True,
        has_workout_plan=True,
    )
    print(f"[시나리오 2 - 탈수 주의] 점수: {score2}점, 등급: {grade2}")
    assert score2 < 50, "탈수 상태는 50점 미만이어야 합니다."
    assert grade2 in ("주의", "위험")

    # 시나리오 3: 활동량 및 환경 보정 권장 수분량 계산 (체중 70kg, 14000보, 운동 60분, 기온 34도)
    rec_ml = HydrationScoreEngine.calculate_recommended_water(
        weight_kg=70.0,
        activity_level="moderate",
        has_coffee_plan=True,
        has_workout_plan=True,
        steps=14000,
        workout_minutes=60,
        temperature_c=34.0,
    )
    print(f"[시나리오 3 - 고활동/폭염 권장량] 권장 수분: {rec_ml}ml ({rec_ml/1000:.2f}L)")
    # 기본: 70*33=2310 + 활동200 + 걸음(4천보*50)=200 + 운동(60분/30*350)=700 + 기온400 + 커피150 = 3960ml -> 3950 or 4000
    assert rec_ml >= 3500, "고활동 및 폭염 시 3.5L 이상이 권장되어야 합니다."

    # 시나리오 4: 서카디언 시간대 매핑 검증
    slot8, prod8, _ = HydrationScoreEngine.get_current_circadian_slot(8)
    slot13, prod13, _ = HydrationScoreEngine.get_current_circadian_slot(13)
    slot18, prod18, _ = HydrationScoreEngine.get_current_circadian_slot(18)
    slot22, prod22, _ = HydrationScoreEngine.get_current_circadian_slot(22)

    assert slot8 == "MORNING" and prod8 == "MORNING_RESET"
    assert slot13 == "DAY" and prod13 == "DAY_FOCUS"
    assert slot18 == "EVENING" and prod18 == "EVENING_RELIEF"
    assert slot22 == "NIGHT" and prod22 == "NIGHT_CALM"

    print("=== 모든 단위 시나리오 검증 통과 성공! ===")


if __name__ == "__main__":
    test_hydration_engine_scenarios()
