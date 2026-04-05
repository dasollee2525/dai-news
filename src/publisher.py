"""
GitHub Pages 퍼블리셔
JSON 데이터 → HTML로 변환하여 docs/ 에 저장

생성 파일:
  docs/index.html          : 항상 최신 뉴스 (GitHub Pages 메인)
  docs/YYYY-MM-DD.html     : 날짜별 아카이브 페이지
  docs/archive.html        : 전체 날짜 목록
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "docs"
DAILY_DIR = BASE_DIR / "data" / "daily"
ARCHIVE_INDEX = BASE_DIR / "data" / "archive" / "index.json"

CATEGORY_COLOR = {
    "AI도구활용": "#6366f1",
    "데이터분석": "#0ea5e9",
    "LLM응용":   "#8b5cf6",
    "생산성":    "#10b981",
    "AI트렌드":  "#f59e0b",
    "기타":      "#6b7280",
}

CATEGORY_EMOJI = {
    "AI도구활용": "🛠️",
    "데이터분석": "📊",
    "LLM응용":   "🤖",
    "생산성":    "⚡",
    "AI트렌드":  "📡",
    "기타":      "📌",
}


def _base_html(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans KR", sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      min-height: 100vh;
      line-height: 1.6;
    }}

    /* ── 헤더 ── */
    header {{
      background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
      border-bottom: 1px solid #1e293b;
      padding: 28px 24px;
      text-align: center;
    }}
    header .logo {{ font-size: 13px; color: #6366f1; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 8px; }}
    header h1 {{ font-size: 26px; font-weight: 700; color: #f8fafc; }}
    header .meta {{ font-size: 13px; color: #64748b; margin-top: 6px; }}
    header nav {{ margin-top: 16px; }}
    header nav a {{
      display: inline-block;
      margin: 0 8px;
      font-size: 13px;
      color: #94a3b8;
      text-decoration: none;
      padding: 4px 12px;
      border: 1px solid #1e293b;
      border-radius: 20px;
      transition: all 0.2s;
    }}
    header nav a:hover {{ color: #e2e8f0; border-color: #6366f1; background: rgba(99,102,241,0.1); }}

    /* ── 본문 ── */
    main {{
      max-width: 760px;
      margin: 0 auto;
      padding: 36px 20px 60px;
    }}

    /* ── 카드 ── */
    .card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 14px;
      padding: 24px;
      margin-bottom: 20px;
      transition: border-color 0.2s, transform 0.2s;
    }}
    .card:hover {{ border-color: #6366f1; transform: translateY(-2px); }}

    .card-header {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 14px;
    }}
    .card-number {{
      flex-shrink: 0;
      width: 28px; height: 28px;
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 700;
      color: #6366f1;
      display: flex; align-items: center; justify-content: center;
    }}
    .card-title {{
      font-size: 16px;
      font-weight: 700;
      color: #f1f5f9;
      line-height: 1.4;
    }}

    .badge {{
      display: inline-block;
      font-size: 11px;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 20px;
      margin-bottom: 12px;
      color: #fff;
    }}

    .summary {{
      font-size: 14px;
      color: #94a3b8;
      line-height: 1.75;
      margin-bottom: 16px;
    }}

    .card-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 8px;
      padding-top: 14px;
      border-top: 1px solid #334155;
    }}
    .source-info {{ font-size: 12px; color: #64748b; }}
    .source-info span {{ color: #475569; margin: 0 6px; }}

    .read-btn {{
      display: inline-block;
      font-size: 12px;
      font-weight: 600;
      color: #6366f1;
      text-decoration: none;
      padding: 6px 16px;
      border: 1px solid #6366f1;
      border-radius: 8px;
      transition: all 0.2s;
    }}
    .read-btn:hover {{ background: #6366f1; color: #fff; }}

    /* ── 아카이브 테이블 ── */
    .archive-table {{ width: 100%; border-collapse: collapse; }}
    .archive-table th, .archive-table td {{
      padding: 12px 16px;
      text-align: left;
      border-bottom: 1px solid #1e293b;
      font-size: 14px;
    }}
    .archive-table th {{ color: #64748b; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
    .archive-table td a {{ color: #6366f1; text-decoration: none; }}
    .archive-table td a:hover {{ text-decoration: underline; }}

    /* ── 푸터 ── */
    footer {{
      text-align: center;
      font-size: 12px;
      color: #334155;
      padding: 24px;
      border-top: 1px solid #1e293b;
    }}
  </style>
</head>
<body>
  <header>
    <div class="logo">DAI Guild</div>
    <h1>데이터 분석 AI 길드 뉴스</h1>
    <div class="meta">데이터 분석가를 위한 AI 실무 뉴스 큐레이션</div>
    <nav>
      <a href="index.html">최신 뉴스</a>
      <a href="archive.html">아카이브</a>
    </nav>
  </header>
  <main>
    {body}
  </main>
  <footer>자동 수집 · OpenAI 큐레이션 · DAI Guild</footer>
</body>
</html>"""


def _card_html(article: dict, index: int) -> str:
    category  = article.get("category", "기타")
    color     = CATEGORY_COLOR.get(category, "#6b7280")
    emoji     = CATEGORY_EMOJI.get(category, "📌")
    region    = "🇰🇷" if article.get("region") == "domestic" else "🌐"
    score     = article.get("score", "-")
    title     = article["title"].replace("<", "&lt;").replace(">", "&gt;")
    summary   = article.get("summary_ko", "").replace("<", "&lt;").replace(">", "&gt;")
    source    = article.get("source", "")
    pub       = article.get("published_at", "")[:10] if article.get("published_at") else ""

    return f"""
    <div class="card">
      <div class="card-header">
        <div class="card-number">{index}</div>
        <div class="card-title">{title}</div>
      </div>
      <div>
        <span class="badge" style="background:{color}">{emoji} {category}</span>
      </div>
      <p class="summary">{summary}</p>
      <div class="card-footer">
        <div class="source-info">{region} {source}<span>·</span>{pub}<span>·</span>관련도 {score}점</div>
        <a class="read-btn" href="{article['link']}" target="_blank" rel="noopener">원문 보기 →</a>
      </div>
    </div>"""


def _daily_body(data: dict) -> str:
    date_str = data["date"]
    articles = data["articles"]
    try:
        dt = datetime.fromisoformat(date_str)
        date_ko = dt.strftime("%Y년 %m월 %d일")
    except Exception:
        date_ko = date_str

    cards = "\n".join(_card_html(a, i+1) for i, a in enumerate(articles))
    return f"""
    <div style="margin-bottom:28px;">
      <h2 style="font-size:20px;font-weight:700;color:#f1f5f9;">📰 {date_ko} 뉴스</h2>
      <p style="font-size:13px;color:#64748b;margin-top:4px;">총 {len(articles)}개 선별</p>
    </div>
    {cards}"""


def publish(date_str: str = None):
    if date_str is None:
        date_str = datetime.now(KST).strftime("%Y-%m-%d")

    daily_path = DAILY_DIR / f"{date_str}.json"
    if not daily_path.exists():
        print(f"  [경고] {daily_path} 파일이 없습니다. publish 건너뜀.")
        return

    with open(daily_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        dt = datetime.fromisoformat(date_str)
        date_ko = dt.strftime("%Y년 %m월 %d일")
    except Exception:
        date_ko = date_str

    body    = _daily_body(data)
    page    = _base_html(f"DAI 길드 뉴스 — {date_ko}", body)

    # index.html (최신)
    (DOCS_DIR / "index.html").write_text(page, encoding="utf-8")
    print(f"  생성: docs/index.html")

    # YYYY-MM-DD.html (아카이브)
    (DOCS_DIR / f"{date_str}.html").write_text(page, encoding="utf-8")
    print(f"  생성: docs/{date_str}.html")

    _update_archive_page()


def _update_archive_page():
    if not ARCHIVE_INDEX.exists():
        return

    with open(ARCHIVE_INDEX, "r", encoding="utf-8") as f:
        index = json.load(f)

    entries = index.get("entries", [])
    rows = ""
    for e in entries:
        rows += f'<tr><td><a href="{e["date"]}.html">{e["date"]}</a></td><td>{e.get("count","-")}개</td></tr>\n'

    body = f"""
    <div style="margin-bottom:28px;">
      <h2 style="font-size:20px;font-weight:700;color:#f1f5f9;">📂 전체 아카이브</h2>
    </div>
    <div style="background:#1e293b;border:1px solid #334155;border-radius:14px;overflow:hidden;">
      <table class="archive-table">
        <thead><tr><th>날짜</th><th>기사 수</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""

    (DOCS_DIR / "archive.html").write_text(
        _base_html("DAI 길드 뉴스 아카이브", body), encoding="utf-8"
    )
    print(f"  생성: docs/archive.html")
