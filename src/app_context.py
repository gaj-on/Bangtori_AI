"""
 Copyright (c) 2025. Ebee1205(wavicle) all rights reserved.

 The copyright of this software belongs to Ebee1205(wavicle).
 All rights reserved.
"""

# app_context.py
import orjson

from pydantic import BaseModel
from typing import Any
from typing import Optional

import modules.logger as logger

class LoggerConfig(BaseModel):
    level: str
    path: str
    suffix: str
    max_bytes: int
    max_files: str
    rotation: str
    use_console: bool

class HTTPConfig(BaseModel):
    allow_origins: list[str]
    allow_methods: list[str]
    allow_headers: list[str]
    allow_credentials: bool

class AppConfig(BaseModel):
    # 상위 항목 직접 정의
    environment: str
    project_name: str
    api_v1_str: str
    host: str
    port: int
    secret_key: str
    access_token_expire_minutes: int

    # 구성 요소들
    logger: LoggerConfig
    http_config: Optional[HTTPConfig] = None

    # 시스템 모니터링 관련 기본값 설정
    enable_monitoring: Optional[bool] = True
    monitoring_interval: Optional[int] = 10

    # 서비스 관련

class AppContext:
    def __init__(self):
        self.cfg = {}
        self.log = None
        
        # 핸들러

        # 매니저
        self.system_monitor = None

        # 서비스
        # self.llm_manager = {}

    def load_config(self, path: str) -> AppConfig:
        """JSON 파일을 로드하고 AppConfig 모델로 파싱"""
        print("+ start load cfg")

        with open(path, "rb") as f:
            raw = orjson.loads(f.read())

        print("- end load cfg")
        self.cfg = AppConfig(**raw)
        
    def load_json_map(self, name: str, path: str):
        """
        임의의 JSON 파일을 로드하여 ctx에 동적으로 등록
        예: ctx.load_json_map("event_map", "config/event_map.json")
            → self.event_map 로 저장됨
        """
        try:
            with open(path, "rb") as f:
                data = orjson.loads(f.read())

            setattr(self, name, data)
            print(f"> loaded JSON map '{name}' from {path}")
            return True
        except Exception as e:
            print(f"!! failed to load JSON map '{name}' from {path}: {e}")
            return False

    def _init_logger(self):
        print("+ start init logger")

        log_level = self.cfg.logger.level 
        log_path = self.cfg.logger.path
        log_max_files = self.cfg.logger.max_files
        self.log = logger.setup_logger(log_level, log_path, log_max_files)

        self.log.debug("- end init logger")

    def _init_llms(self):
        self.log.debug("+ start init LLMs")

        self.llm_manager = {}
