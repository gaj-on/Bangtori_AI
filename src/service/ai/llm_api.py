# api 기본 예제
# service/api/analyze_api.py

from fastapi import APIRouter, Request

import src.common.common_codes as codes

# 라우터 등록은 여기서 하고 실제 로직은 service에서 관리
# http://localhost:8000/

router = APIRouter(prefix="/v1/analyze", tags=["analyze"])

# GET /v1/analyze/test
@router.get("/test")
async def test(request: Request):
    ctx = request.app.state.ctx
    mgr = ctx.llm_manager
    return await mgr.generate("한 줄 인사 해줘", temperature=0.7)