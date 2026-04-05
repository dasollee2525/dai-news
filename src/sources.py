"""
뉴스 소스 및 키워드 로더
실제 데이터는 config/sources.json 에서 관리합니다.

소스 추가/수정/비활성화 방법:
  config/sources.json 파일을 직접 편집하세요.
  - active: false 로 설정하면 수집에서 제외됩니다.
  - 코드 변경 없이 소스를 추가할 수 있습니다.
"""

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "sources.json"


def _load_config() -> dict:
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(f"sources.json 파일을 찾을 수 없습니다: {_CONFIG_PATH}")
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_sources() -> list[dict]:
    """active: true 인 소스만 반환"""
    config = _load_config()
    return [s for s in config["sources"] if s.get("active", True)]


def get_include_keywords() -> list[str]:
    return _load_config()["filters"]["include_keywords"]


def get_exclude_keywords() -> list[str]:
    return _load_config()["filters"]["exclude_keywords"]


# collector.py 하위 호환을 위한 모듈 레벨 변수
SOURCES = get_sources()
INCLUDE_KEYWORDS = get_include_keywords()
EXCLUDE_KEYWORDS = get_exclude_keywords()
