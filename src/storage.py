"""
JSON 저장 모듈
data/daily/YYYY-MM-DD.json 에 저장
data/archive/index.json 에 날짜별 인덱스 유지
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

KST = timezone(timedelta(hours=9))
BASE_DIR = Path(__file__).parent.parent
DAILY_DIR = BASE_DIR / "data" / "daily"
ARCHIVE_INDEX = BASE_DIR / "data" / "archive" / "index.json"


def save_daily(articles: list[dict], date_str: str = None) -> Path:
    """
    선별된 기사를 날짜별 JSON 파일로 저장.
    date_str: 'YYYY-MM-DD' 형식. None이면 오늘(KST) 날짜 사용.
    """
    if date_str is None:
        date_str = datetime.now(KST).strftime("%Y-%m-%d")

    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DAILY_DIR / f"{date_str}.json"

    payload = {
        "date": date_str,
        "generated_at": datetime.now(KST).isoformat(),
        "count": len(articles),
        "articles": articles,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"  저장 완료: {output_path}")
    _update_index(date_str, len(articles))
    return output_path


def _update_index(date_str: str, count: int):
    """archive/index.json 에 날짜별 메타 정보 추가"""
    ARCHIVE_INDEX.parent.mkdir(parents=True, exist_ok=True)

    if ARCHIVE_INDEX.exists():
        with open(ARCHIVE_INDEX, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"entries": []}

    # 같은 날짜 중복 방지
    index["entries"] = [e for e in index["entries"] if e["date"] != date_str]
    index["entries"].append({"date": date_str, "count": count})
    index["entries"].sort(key=lambda x: x["date"], reverse=True)

    with open(ARCHIVE_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def load_daily(date_str: str) -> Optional[dict]:
    """날짜 문자열로 저장된 뉴스 로드"""
    path = DAILY_DIR / f"{date_str}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
