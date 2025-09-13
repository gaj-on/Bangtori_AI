# api 기본 예제
# service/api/analyze_api.py

from fastapi import APIRouter, Request

import src.common.common_codes as codes
from src.service.ai.asset.prompts.prompts_cfg import (SYSTEM_PROMPTS, DAILY_REPORT_PROMPTS, MONTHLY_REPORT_PROMPTS)


# 라우터 등록은 여기서 하고 실제 로직은 service에서 관리
# http://localhost:8000/

router = APIRouter(prefix="/v1/analyze", tags=["analyze"])

# GET /v1/analyze/dailyReport
@router.get("/dailyReport")
async def dailyReport(request: Request):
    ctx = request.app.state.ctx
    mgr = ctx.llm_manager

    return await mgr.generate(
        DAILY_REPORT_PROMPTS,
        placeholders={
            "metrics": {
                "dust": [12, 14, 20, 18],
                "co2": [600, 720, 680, 650], 
                "tvoc": [600, 720, 680, 650], 
                "temp": [24.1, 24.3, 23.9, 24.0],
                "humi": [45, 48, 50, 46] 
            }
        },
        temperature=0.7
    )

# GET /v1/analyze/monthlyReport
@router.get("/monthlyReport")
async def monthlyReport(request: Request):
    ctx = request.app.state.ctx
    mgr = ctx.llm_manager

    return await mgr.generate(
        DAILY_REPORT_PROMPTS,
        placeholders={
            "input_data": {
                "pm25": [12, 14, 20, 18],
                "co2": [600, 720, 680, 650], 
                "temperature": [24.1, 24.3, 23.9, 24.0],
                "humidity": [45, 48, 50, 46] 
            }
        },
        temperature=0.7
    )
