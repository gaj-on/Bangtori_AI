# api 기본 예제
# service/api/analyze_api.py

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Iterable, Any

import httpx
from fastapi import APIRouter, HTTPException, Request

import src.common.common_codes as codes
from src.service.ai.asset.prompts.prompts_cfg import (SYSTEM_PROMPTS, 
                                                      DAILY_REPORT_PROMPTS, 
                                                      MONTHLY_REPORT_PROMPTS, 
                                                      GENERATE_TIP_REPORT)

# 라우터 등록은 여기서 하고 실제 로직은 service에서 관리
# http://localhost:8000/

router = APIRouter(prefix="/api/analyze", tags=["analyze"])

# GET /api/analyze/dailyReport
@router.get("/dailyReport")
async def daily_report(request: Request):
    ctx = request.app.state.ctx
    base_url = getattr(ctx, "host", "https://bangtori-be.onrender.com/api")

    # 오늘 0시~내일 0시 (서울 고정)
    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    start_dt = datetime(today.year, today.month, today.day, tzinfo=ZoneInfo("Asia/Seoul"))
    end_dt = start_dt + timedelta(days=1)

    start_epoch = int(start_dt.timestamp())
    end_epoch = int(end_dt.timestamp())

    metrics_url = f"{base_url}/telemetry/range"
    device_url = f"{base_url}/appliances"
    m_params = {"from": start_epoch, "toExclusive": end_epoch}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # telemetry
            m_r = await client.get(metrics_url, params=m_params)
            m_r.raise_for_status()
            m_payload = m_r.json()
            metrics = parse_metrics(m_payload)  

            # # devices
            # d_r = await client.get(device_url)
            # d_r.raise_for_status()
            # d_payload = d_r.json()             
            # device_status = parse_device_status(d_payload)

            resp_text = await ctx.llm_manager.generate(
                DAILY_REPORT_PROMPTS,
                placeholders={
                    "metrics": metrics,
                    # "deviceStatus": device_status
                },
                temperature=0.7
            )
            return ctx.llm_manager.parse_reports(resp_text)
        
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Telemetry backend call failed: {e}")


# GET /api/analyze/monthlyReport
@router.get("/monthlyReport")
async def monthlyReport(request: Request):
    ctx = request.app.state.ctx
    mgr = ctx.llm_manager
    base_url = getattr(ctx, "host", "https://bangtori-be.onrender.com/api")

    # 이번 달 1일 ~ 다음 달 1일 (서울 고정)
    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    start_dt = datetime(today.year, today.month, 1, tzinfo=ZoneInfo("Asia/Seoul"))

    if today.month == 12:  # 12월이면 다음 해 1월
        end_dt = datetime(today.year + 1, 1, 1, tzinfo=ZoneInfo("Asia/Seoul"))
    else:
        end_dt = datetime(today.year, today.month + 1, 1, tzinfo=ZoneInfo("Asia/Seoul"))

    start_epoch = int(start_dt.timestamp())
    end_epoch = int(end_dt.timestamp())

    metrics_url = f"{base_url}/telemetry/range"
    m_params = {"from": start_epoch, "toExclusive": end_epoch}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # 1달치 telemetry 데이터 조회
            m_r = await client.get(metrics_url, params=m_params)
            m_r.raise_for_status()
            m_payload = m_r.json()
            metrics = parse_metrics(m_payload)

        # LLM 프롬프트 생성
        resp_text = await mgr.generate(
            MONTHLY_REPORT_PROMPTS,
            placeholders={
                "metrics": metrics,
                "time_range": {
                    "start": start_dt.strftime("%Y-%m-%d"),
                    "end": (end_dt - timedelta(days=1)).strftime("%Y-%m-%d")
                }
            },
            temperature=0.7
        )

        return mgr.parse_reports(resp_text)

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Monthly telemetry backend call failed: {e}")


# GET /api/tip/category
@router.get("/tip/category")
async def tip_category(request: Request):
    ctx = request.app.state.ctx
    base_url = getattr(ctx, "host", "https://bangtori-be.onrender.com/api")

    # 오늘 0시~내일 0시 (서울 고정)
    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    start_dt = datetime(today.year, today.month, today.day, tzinfo=ZoneInfo("Asia/Seoul"))
    end_dt = start_dt + timedelta(days=1)

    start_epoch = int(start_dt.timestamp())
    end_epoch = int(end_dt.timestamp())

    metrics_url = f"{base_url}/telemetry/range"
    m_params = {"from": start_epoch, "toExclusive": end_epoch}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # telemetry
            m_r = await client.get(metrics_url, params=m_params)
            m_r.raise_for_status()
            m_payload = m_r.json()
            metrics = parse_metrics(m_payload)  

            resp_text = await ctx.llm_manager.generate(
                GENERATE_TIP_REPORT,
                placeholders={
                    "metrics": metrics,
                },
                temperature=0.7
            )
            return ctx.llm_manager.parse_reports(resp_text)
        
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Telemetry backend call failed: {e}")


def parse_metrics(payload: dict) -> dict:
    metrics = {
        "dust":  [point["value"] for point in payload.get("series", {}).get("dust", [])],
        "co2":   [point["value"] for point in payload.get("series", {}).get("co2", [])],
        "tvoc":  [point["value"] for point in payload.get("series", {}).get("tvoc", [])],
        "temp":  [point["value"] for point in payload.get("series", {}).get("temp", [])],
        "humi":  [point["value"] for point in payload.get("series", {}).get("humi", [])],
    }

    return metrics

def parse_device_status(items: Iterable[dict]) -> Dict[str, bool]:
    summary: Dict[str, bool] = {}
    for it in items or []:
        try:
            dev_type = str(it.get("type", "")).strip()
            if not dev_type:
                continue
            key = dev_type.upper()
            on = bool(it.get("on", False))
            # 하나라도 True면 True
            summary[key] = summary.get(key, False) or on
        except Exception:
            # 단일 항목 오류는 무시하고 계속
            continue
    return summary