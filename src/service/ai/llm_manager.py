from __future__ import annotations
import time, json
from enum import Enum
from typing import Optional, Dict, Any, Callable, Awaitable
from pydantic import BaseModel
from src.service.ai.llm_manager import SystemPrompts

# ---- 외부에서 제공되는 SystemPrompts/PromptTemplate을 그대로 사용 ----
# from your_module import SystemPrompts  # 사용자 제공 클래스 사용
# 이 예제에서는 같은 파일에 있다고 가정
# class SystemPrompts: ...

class LLMResponse(BaseModel):
    content: str   # 최종 텍스트 (JSON 모드면 pretty-JSON 문자열)
    model: str
    tokens: int
    latency: float

class PromptMode(str, Enum):
    PLAIN = "plain"                 # 유저 프롬프트만 전달
    INTRO = "intro"                 # system:intro + user
    DATE = "date"                   # system:date + user
    JSON = "json"                   # system:json + user (JSON 출력 유도)
    INTRO_DATE_JSON = "intro_date_json"  # intro + date + json + user

class LLMManager:
    """
    - provider: async (prompt:str, **kwargs) -> str
    - mode에 따라 system 프롬프트들을 합성하고, 출력 후처리(JSON pretty)까지 수행
    """
    def __init__(self, ctx, provider: Callable[..., Awaitable[str]], model_key: str = "default-llm"):
        self.ctx = ctx
        self.log = ctx.log
        self.provider = provider
        self.model_key = model_key

    async def generate(self, user_prompt: str, *, mode: PromptMode = PromptMode.PLAIN, **kwargs) -> LLMResponse:
        start = time.time()
        try:
            final_prompt = self._build_prompt(user_prompt, mode=mode, extra=kwargs.get("extra"))
            raw = await self.provider(final_prompt, **kwargs)
            out_text = self._postprocess_output(raw, mode=mode)
            return LLMResponse(
                content=out_text,
                model=self.model_key,
                tokens=max(1, len(out_text.split())),
                latency=time.time() - start
            )
        except Exception as e:
            self.log.error(f"[LLM] error: {e}")
            raise

    # ---- 내부: 프롬프트 합성 (in) ----
    def _build_prompt(self, user_prompt: str, *, mode: PromptMode, extra: Optional[Dict[str, Any]] = None) -> str:
        def fmt(tpl: str) -> str:
            if extra and isinstance(extra, dict):
                try:
                    return tpl.format(**extra)
                except Exception:
                    return tpl
            return tpl

        match mode:
            case PromptMode.PLAIN:
                return user_prompt

            case PromptMode.INTRO:
                return f"""
                    [SYSTEM]
                    {fmt(SystemPrompts.templates["intro"].content)}

                    [USER]
                    {user_prompt}
                """

            case PromptMode.DATE:
                return f"""
                    [SYSTEM]
                    {fmt(SystemPrompts.templates["date"].content)}

                    [USER]
                    {user_prompt}
                """

            case PromptMode.JSON:
                return f"""
                    [SYSTEM]
                    {fmt(SystemPrompts.templates["json"].content)}

                    [USER]
                    {user_prompt}
                """

            case PromptMode.INTRO_DATE_JSON:
                return f"""
                    [SYSTEM]
                    {fmt(SystemPrompts.templates["intro"].content)}

                    [SYSTEM]
                    {fmt(SystemPrompts.templates["date"].content)}

                    [SYSTEM]
                    {fmt(SystemPrompts.templates["json"].content)}

                    [USER]
                    {user_prompt}
                """

        return user_prompt

    # ---- 내부: 출력 후처리 (out) ----
    def _postprocess_output(self, raw: str, *, mode: PromptMode) -> str:
        # JSON 모드류는 JSON 파싱 후 pretty string으로 반환(실패 시 원문 유지)
        if mode in (PromptMode.JSON, PromptMode.INTRO_DATE_JSON):
            try:
                parsed = json.loads(raw)
                return json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                return raw
        # 나머지는 그대로
        return raw

# -------------------------------
# 사용 예시
# -------------------------------
# 더미 provider
async def echo_provider(prompt: str, **kwargs) -> str:
    # 실제에선 OpenAI/Ollama 클라이언트를 호출
    # JSON 모드 테스트를 위해 간단한 응답 분기
    if "JSON 출력" in prompt or "[SYSTEM]" in prompt and "JSON" in prompt:
        return '{"input":"hello","date":"2025-09-12","response":"ok"}'
    return f"[echo] {prompt}"

class DummyCtx:
    def __init__(self):
        class _Log:
            def info(self, *a): print(*a)
            def error(self, *a): print(*a)
        self.log = _Log()

# 예:
# ctx = DummyCtx()
# ctx.llm = LLMManager(ctx, provider=echo_provider, model_key="mini")
# resp1 = await ctx.llm.generate("안녕!", mode=PromptMode.PLAIN)
# resp2 = await ctx.llm.generate("데이터를 요약해줘", mode=PromptMode.INTRO_DATE_JSON)
# print(resp1.content)
# print(resp2.content)
