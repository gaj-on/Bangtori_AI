# llm_manager.py
import ollama
from asyncio import to_thread

class LLMManager:
    def __init__(self, ctx, provider: str, model: str):
        self.ctx = ctx
        self.model = model

    async def generate(self, prompt: str, **options) -> str:
        """프롬프트 그대로 보내고 텍스트만 반환"""
        def _call():
            args = {"model": self.model, "prompt": prompt}
            if options:
                args["options"] = options
            return ollama.generate(**args)
        return (await to_thread(_call)).get("response", "")
