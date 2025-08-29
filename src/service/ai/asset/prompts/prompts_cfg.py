from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel
import system_prompts

class PromptTemplate(BaseModel):
    name: str
    content: str
    description: Optional[str]
    parameters: Optional[Dict[str, str]]

class PromptCategory(str, Enum):
    SYSTEM = "system"
    USER = "user"
    FUNCTION = "function"

class SystemPrompts:
    templates: Dict[str, PromptTemplate] = {
        "intro": PromptTemplate(
            name="intro",
            content=system_prompts.INTRO_PROMPT,
            description="초기 설정 프롬프트"
        ),
        "date": PromptTemplate(
            name="date",
            content=system_prompts.AUTO_DATE_PROMPT,
            description="날짜 자동 할당 프롬프트"
        ),
        "json": PromptTemplate(
            name="json",
            content=system_prompts.JSON_OUTPUT_PROMPT,
            description="JSON 출력 포맷 프롬프트",
            parameters={
                "format": "json",
                "required_fields": "input,date,response"
            }
        )
    }

    @classmethod
    def get(cls, name: str) -> Optional[PromptTemplate]:
        return cls.templates.get(name)