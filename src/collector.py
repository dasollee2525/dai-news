"""
RSS 피드 수집 모듈
소스 목록은 config/sources.json 에서 로드합니다.
"""

import feedparser
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional
from sources import get_sources, get_include_keywords, get_exclude_keywords


KST = timezone(timedelta(hours=9))


def _is_recent(entry, hours: int = 48) -> bool:
    """최근 N시간 이내 기사인지 확인"""
    for time_field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, time_field, None)
        if t:
            pub = datetime(*t[:6], tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - pub).total_seconds() < hours * 3600
    return True  # 날짜 정보 없으면 일단 포함


def _passes_keyword_filter(text: str, include_kws: list, exclude_kws: list) -> bool:
    """1차 키워드 필터 - 매 실행마다 JSON에서 최신 키워드 반영"""
    text_lower = text.lower()

    for kw in exclude_kws:
        if kw.lower() in text_lower:
            return False

    for kw in include_kws:
        if kw.lower() in text_lower:
            return True

    return False


def _parse_entry(entry, source: dict, include_kws: list, exclude_kws: list) -> Optional[dict]:
    """feedparser entry → 정규화된 dict"""
    title = getattr(entry, "title", "").strip()
    link = getattr(entry, "link", "").strip()
    summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
    summary = summary.strip()

    if not title or not link:
        return None

    combined = f"{title} {summary}"

    # 영어 소스는 exclude 키워드만 걸러내고 LLM에게 판단 위임
    # (한국어 키워드 include 필터가 영어 기사를 과도하게 차단하는 문제 방지)
    if source.get("lang") == "en":
        if any(kw.lower() in combined.lower() for kw in exclude_kws):
            return None
    else:
        if not _passes_keyword_filter(combined, include_kws, exclude_kws):
            return None

    pub_time = None
    for time_field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, time_field, None)
        if t:
            pub_time = datetime(*t[:6], tzinfo=timezone.utc).astimezone(KST).isoformat()
            break

    return {
        "title": title,
        "link": link,
        "summary_raw": summary[:500],  # 원문 요약 (앞 500자)
        "source": source["name"],
        "lang": source["lang"],
        "region": source["region"],
        "published_at": pub_time,
    }


def collect(hours: int = 48) -> list[dict]:
    """
    모든 소스에서 뉴스를 수집하고 1차 필터를 통과한 기사 목록 반환.
    sources.json 을 매 실행 시 읽으므로, 코드 재시작 없이 소스/키워드 변경이 반영됩니다.
    hours: 최근 몇 시간 이내 기사만 수집할지
    """
    # 매 실행마다 JSON에서 최신 소스/키워드 로드
    sources = get_sources()
    include_kws = get_include_keywords()
    exclude_kws = get_exclude_keywords()

    print(f"  로드된 소스: {len(sources)}개")
    candidates = []

    for source in sources:
        print(f"  수집 중: {source['name']}")
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries:
                if not _is_recent(entry, hours=hours):
                    continue
                article = _parse_entry(entry, source, include_kws, exclude_kws)
                if article:
                    candidates.append(article)
        except Exception as e:
            print(f"  [경고] {source['name']} 수집 실패: {e}")

    # 중복 URL 제거
    seen = set()
    unique = []
    for a in candidates:
        if a["link"] not in seen:
            seen.add(a["link"])
            unique.append(a)

    print(f"  1차 필터 통과: {len(unique)}개")
    return unique
