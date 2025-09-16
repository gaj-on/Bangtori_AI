# api 기본 예제
# service/api/analyze_api.py

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, HTTPException, Request

import src.common.common_codes as codes
from src.service.ai.asset.prompts.prompts_cfg import (SYSTEM_PROMPTS, DAILY_REPORT_PROMPTS, MONTHLY_REPORT_PROMPTS)


# 라우터 등록은 여기서 하고 실제 로직은 service에서 관리
# http://localhost:8000/

router = APIRouter(prefix="/api/analyze", tags=["analyze"])
base = "https://bangtori-be.onrender.com/api"

# GET /api/analyze/dailyReport
@router.get("/dailyReport")
async def daily_report(request: Request):
    """
    오늘 하루(서울 기준 0시~24시) 구간의 telemetry 데이터를 조회
    """
    ctx = request.app.state.ctx
    telemetry_base = getattr(ctx, "telemetry_base", "https://bangtori-be.onrender.com/api")

    # 오늘 0시~내일 0시 (서울 고정)
    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    start_dt = datetime(today.year, today.month, today.day, tzinfo=ZoneInfo("Asia/Seoul"))
    end_dt = start_dt + timedelta(days=1)

    start_epoch = int(start_dt.timestamp())
    end_epoch = int(end_dt.timestamp())

    # url = f"{telemetry_base}/telemetry/range"
    # params = {"from": start_epoch, "toExclusive": end_epoch}

    # try:
    #     async with httpx.AsyncClient(timeout=10) as client:
    #         r = await client.get(url, params=params)
    #         r.raise_for_status()
    #         payload = r.json()
    # except Exception as e:
    #     raise HTTPException(status_code=502, detail=f"Telemetry backend call failed: {e}")

    # return {
    #     "date": today.isoformat(),
    #     "from": start_epoch,
    #     "toExclusive": end_epoch,
    #     "source": f"{url}?from={start_epoch}&toExclusive={end_epoch}",
    #     "data": payload,
    # }

    resp_text = await ctx.llm_manager.generate(
        DAILY_REPORT_PROMPTS,
        placeholders={
            "metrics": {
                "dust": [12, 14, 20, 18],
                "co2": [600, 720, 680, 650], 
                "tvoc": [600, 720, 680, 650], 
                "temp": [24.1, 24.3, 23.9, 24.0],
                "humi": [45, 48, 50, 46] 
            },
            "deviceStatus": {
                "fan": True,
                "ac": False,
                "robot": False,
                "heat": True
            }
        },
        temperature=0.7
    )

    return ctx.llm_manager.parse_reports(resp_text)

# GET /api/analyze/monthlyReport
@router.get("/monthlyReport")
async def monthlyReport(request: Request):
    ctx = request.app.state.ctx
    mgr = ctx.llm_manager

    resp_text = await mgr.generate(
        MONTHLY_REPORT_PROMPTS,
        placeholders={
            "metrics": {
                "pm25": [12, 14, 20, 18],
                "co2": [600, 720, 680, 650], 
                "temperature": [24.1, 24.3, 23.9, 24.0],
                "humidity": [45, 48, 50, 46] 
            },
            "time_range": {
                "start": "2024-09-01",
                "end": "2024-09-30"
            }
        },
        temperature=0.7
    )

    return ctx.llm_manager.parse_reports(resp_text)
