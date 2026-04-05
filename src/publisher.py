"""
GitHub Pages 퍼블리셔
JSON 데이터 → 마크다운으로 변환하여 docs/ 에 저장

생성 파일:
  docs/index.md          : 항상 최신 뉴스 (GitHub Pages 메인)
  docs/YYYY-MM-DD.md     : 날짜별 아카이브 페이지
  docs/archive.md        : 전체 날짜 목록
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "docs"
DAILY_DIR = BASE_DIR / "data" / "daily"
ARCHIVE_INDEX = BASE_DIR / "data" / "archive" / "index.json"

CATEGORY_EMOJI = {
    "AI도구활용": "🛠️",
    "데이터분석": "📊",
    "LLM응용": "🤖",
    "생산성": "⚡",
    "AI트렌드": "📡",
    "기타": "📌",
}

REGION_LABEL = {
    "domestic": "🇰🇷",
    "international": "🌐",
}


def _format_article(article: dict, index: int) -> str:
    """기사 하나를 마크다운 블록으로 변환"""
    category = article.get("category", "기타")
    emoji = CATEGORY_EMOJI.get(category, "📌")
    region = REGION_LABEL.get(article.get("region", ""), "")
    score = article.get("score", "-")
    stars = "⭐" * int(score) if isinstance(score, int) else ""

    return f"""### {index}. {emoji} {article['title']}

> {article.get('summary_ko', '')}

| 항목 | 내용 |
|------|------|
| 출처 | {region} {article['source']} |
| 카테고리 | {category} |
| 관련도 | {stars} ({score}점) |
| 원문 | [링크 바로가기]({article['link']}) |

"""


def _format_daily_page(data: dict) -> str:
    """하루치 데이터를 전체 마크다운 페이지로 변환"""
    date_str = data["date"]
    articles = data["articles"]
    generated_at = data.get("generated_at", "")

    # 날짜 한국어 포맷
    try:
        dt = datetime.fromisoformat(date_str)
        date_ko = dt.strftime("%Y년 %m월 %d일")
    except Exception:
        date_ko = date_str

    lines = []
    lines.append(f"# 📰 DAI 길드 AI 뉴스 — {date_ko}\n")
    lines.append(f"> 데이터 분석가를 위한 AI 실무 뉴스 큐레이션 | 총 {len(articles)}개\n")
    lines.append("---\n")

    for i, article in enumerate(articles, 1):
        lines.append(_format_article(article, i))

    lines.append("---\n")
    lines.append(f"*자동 생성: {generated_at} | [전체 아카이브](archive.md)*\n")

    return "\n".join(lines)


def publish(date_str: str = None):
    """
    지정된 날짜(또는 오늘)의 JSON을 읽어 GitHub Pages 마크다운 생성.
    - docs/index.md        : 최신 뉴스 (항상 덮어씀)
    - docs/YYYY-MM-DD.md   : 날짜별 아카이브
    - docs/archive.md      : 날짜 목록
    """
    if date_str is None:
        date_str = datetime.now(KST).strftime("%Y-%m-%d")

    daily_path = DAILY_DIR / f"{date_str}.json"
    if not daily_path.exists():
        print(f"  [경고] {daily_path} 파일이 없습니다. publish 건너뜀.")
        return

    with open(daily_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    page_content = _format_daily_page(data)

    # 1. 최신 뉴스 페이지 (index.md)
    index_path = DOCS_DIR / "index.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(page_content)
    print(f"  생성: {index_path}")

    # 2. 날짜별 아카이브 페이지
    archive_page_path = DOCS_DIR / f"{date_str}.md"
    with open(archive_page_path, "w", encoding="utf-8") as f:
        f.write(page_content)
    print(f"  생성: {archive_page_path}")

    # 3. 전체 아카이브 목록 페이지 갱신
    _update_archive_page()


def _update_archive_page():
    """docs/archive.md - 날짜별 링크 목록 갱신"""
    if not ARCHIVE_INDEX.exists():
        return

    with open(ARCHIVE_INDEX, "r", encoding="utf-8") as f:
        index = json.load(f)

    entries = index.get("entries", [])

    lines = ["# 📂 DAI 길드 뉴스 아카이브\n"]
    lines.append("| 날짜 | 기사 수 |\n|------|--------|\n")

    for entry in entries:
        date = entry["date"]
        count = entry.get("count", "-")
        lines.append(f"| [{date}]({date}.md) | {count}개 |\n")

    archive_path = DOCS_DIR / "archive.md"
    with open(archive_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"  생성: {archive_path}")
