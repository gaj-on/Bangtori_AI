import json
import re
import time
import os  # 추가
import google.generativeai as genai  # Gemini 라이브러리 추가
from asyncio import to_thread
from typing import Any, Dict, List, Optional, Union

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")

class LLMManager:
    def __init__(self, ctx, provider: str, model: str):
        self.ctx = ctx
        self.provider = provider
        self.model = model

        if self.provider == "gemini":
            # 보안을 위해 환경 변수에서 API 키를 가져옵니다.
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
            
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel(self.model)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Supported provider is 'gemini'.")

    async def generate(
        self,
        prompt: Union[str, List[str]],
        *,
        placeholders: Optional[Dict[str, Any]] = None,
        **options
    ) -> str:
        final_prompt = self._compose_prompt(prompt, placeholders=placeholders)

        if self.provider == "gemini":
            # Gemini API 옵션을 GenerationConfig로 변환합니다.
            # options 딕셔너리에 있는 키와 값을 기반으로 설정합니다.
            generation_config = genai.types.GenerationConfig(**options)

            def _call_gemini():
                # 동기 함수인 generate_content를 비동기 컨텍스트에서 실행합니다.
                return self.gemini_model.generate_content(
                    final_prompt,
                    generation_config=generation_config
                )

            try:
                response = await to_thread(_call_gemini)
                return response.text
            except Exception as e:
                print(f"Gemini API 호출 중 오류 발생: {e}")
                # 필요한 경우 response.prompt_feedback 등을 통해 추가 정보 확인 가능
                return ""
        
        return "" # __init__에서 provider를 검증하므로 실행될 일 없음

    # ------------------------
    # 내부: 프롬프트 합성 + 치환 (변경 없음)
    # ------------------------
    def _compose_prompt(
        self,
        prompt: Union[str, List[str]],
        *,
        placeholders: Optional[Dict[str, Any]] = None,
    ) -> str:
        if isinstance(prompt, list):
            rendered = [self._render_placeholders(str(p), placeholders) for p in prompt if p]
            return "\n\n".join(rendered)
        return self._render_placeholders(str(prompt), placeholders)

    def _render_placeholders(self, text: str, placeholders: Optional[Dict[str, Any]]) -> str:
        if not placeholders:
            return text

        def _to_str(val: Any) -> str:
            if val is None:
                return ""
            if isinstance(val, (dict, list)):
                return json.dumps(val, ensure_ascii=False, indent=2)
            if isinstance(val, (str, int, float, bool)):
                return str(val)
            return repr(val)

        def repl(m: re.Match) -> str:
            key = m.group(1)
            if key in placeholders:
                return _to_str(placeholders[key])
            return m.group(0)

        return _PLACEHOLDER_RE.sub(repl, text)
    

    
    def parse_reports(self, raw_text: str) -> dict:
        """
        Gemini 응답에서 첫 번째 JSON 블록만 뽑아 time과 함께 반환
        """
        # ```json ... ``` 안쪽 내용 먼저 찾기
        match = re.search(r"```json\s*(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
        if match:
            raw_json = match.group(1).strip()
        else:
            # 없으면 그냥 { } 블록 찾아보기
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            raw_json = match.group(0).strip() if match else "{}"

        try:
            reports = json.loads(raw_json)
        except Exception:
            reports = {}

        return {
            "time": int(time.time()),
            "reports": reports
        }