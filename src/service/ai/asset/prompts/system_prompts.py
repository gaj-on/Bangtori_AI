# 초기 설정
INTRO_PROMPT = """
당신은 
"""

# 날짜/시간 정보 자동 포함
AUTO_DATE_PROMPT = """
## 자동 날짜 할당

사용자가 응답에 날짜를 지정하지 않은 경우, 오늘을 기준으로 한다고 가정한다.
최종 JSON 요약을 생성할 때는 오늘 날짜를 다음 형식으로 표시한다:
"date": "YYYY-MM-DD"
"""

GENERATE_DAILY_REPORT = """

"""

GENERATE_MONTHLY_REPORT = """

"""

GENERATE_PHOTO_REPORT = """

"""


# 응답을 JSON 형식으로 저장
JSON_OUTPUT_PROMPT = """
사용자의 모든 답변을 다음 키를 가지는 JSON 객체로 요약:
"input", "date", "response"
"""
