"""
GitHub Pages 퍼블리셔
JSON 데이터 → HTML로 변환하여 docs/ 에 저장
- 좌측 사이드바: 카테고리 필터 + 날짜 정렬
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
    "AI도구활용":   "#6366f1",
    "데이터분석+AI": "#0ea5e9",
    "LLM응용":     "#8b5cf6",
    "생산성":      "#10b981",
    "AI트렌드":    "#f59e0b",
    "기타":        "#6b7280",
}
CATEGORY_EMOJI = {
    "AI도구활용":   "🛠️",
    "데이터분석+AI": "📊",
    "LLM응용":     "🤖",
    "생산성":      "⚡",
    "AI트렌드":    "📡",
    "기타":        "📌",
}


def _base_html(title: str, sidebar: str, body: str, date_nav: str = "") -> str:
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
      background: #0f172a; color: #e2e8f0; min-height: 100vh; line-height: 1.6;
    }}

    /* ── 헤더 ── */
    header {{
      background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
      border-bottom: 1px solid #1e293b;
      padding: 24px 28px; text-align: center;
    }}
    header .logo {{ font-size: 12px; color: #6366f1; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px; }}
    header h1 {{ font-size: 24px; font-weight: 700; color: #f8fafc; }}
    header .meta {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
    header nav {{ margin-top: 14px; }}
    header nav a {{
      display: inline-block; margin: 0 6px; font-size: 13px; color: #94a3b8;
      text-decoration: none; padding: 4px 14px; border: 1px solid #1e293b;
      border-radius: 20px; transition: all 0.2s;
    }}
    header nav a:hover {{ color: #e2e8f0; border-color: #6366f1; background: rgba(99,102,241,0.1); }}

    /* ── 날짜 네비게이션 ── */
    .date-nav {{
      display: flex; align-items: center; justify-content: center;
      gap: 12px; margin-top: 16px;
    }}
    .date-nav a, .date-nav span {{
      font-size: 13px; color: #94a3b8; text-decoration: none;
      padding: 5px 14px; border: 1px solid #1e293b;
      border-radius: 20px; transition: all 0.2s;
    }}
    .date-nav a:hover {{ color: #e2e8f0; border-color: #6366f1; background: rgba(99,102,241,0.1); }}
    .date-nav .current {{ color: #f1f5f9; border-color: #6366f1; background: rgba(99,102,241,0.15); font-weight: 600; }}
    .date-nav .disabled {{ color: #334155; border-color: #1e293b; cursor: default; pointer-events: none; }}

    /* ── 레이아웃 ── */
    .layout {{
      display: flex;
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 60px;
      gap: 28px;
      align-items: flex-start;
    }}

    /* ── 사이드바 ── */
    .sidebar {{
      width: 220px;
      flex-shrink: 0;
      position: sticky;
      top: 24px;
    }}
    .sidebar-section {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 14px;
      padding: 18px;
      margin-bottom: 16px;
    }}
    .sidebar-title {{
      font-size: 11px; font-weight: 600; color: #64748b;
      text-transform: uppercase; letter-spacing: 0.08em;
      margin-bottom: 14px;
    }}
    .filter-btn {{
      display: flex; align-items: center; gap: 8px;
      width: 100%; padding: 8px 10px; margin-bottom: 4px;
      background: transparent; border: 1px solid transparent;
      border-radius: 8px; color: #94a3b8; font-size: 13px;
      cursor: pointer; text-align: left; transition: all 0.15s;
    }}
    .filter-btn:hover {{ background: #0f172a; border-color: #334155; color: #e2e8f0; }}
    .filter-btn.active {{ background: #0f172a; border-color: #6366f1; color: #e2e8f0; }}
    .filter-btn .dot {{
      width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    }}
    .filter-btn .count {{
      margin-left: auto; font-size: 11px; color: #475569;
      background: #0f172a; padding: 1px 7px; border-radius: 10px;
    }}
    .sort-btn {{
      display: flex; align-items: center; gap: 6px;
      width: 100%; padding: 8px 10px; margin-bottom: 4px;
      background: transparent; border: 1px solid transparent;
      border-radius: 8px; color: #94a3b8; font-size: 13px;
      cursor: pointer; text-align: left; transition: all 0.15s;
    }}
    .sort-btn:hover {{ background: #0f172a; border-color: #334155; color: #e2e8f0; }}
    .sort-btn.active {{ background: #0f172a; border-color: #6366f1; color: #e2e8f0; }}

    /* ── 메인 콘텐츠 ── */
    main {{ flex: 1; min-width: 0; }}

    /* ── 카드 ── */
    .card {{
      background: #1e293b; border: 1px solid #334155; border-radius: 14px;
      padding: 24px; margin-bottom: 20px; transition: border-color 0.2s, transform 0.2s;
    }}
    .card:hover {{ border-color: #6366f1; transform: translateY(-2px); }}
    .card[data-hidden="true"] {{ display: none; }}
    .card-header {{ display: flex; align-items: flex-start; gap: 12px; margin-bottom: 14px; }}
    .card-number {{
      flex-shrink: 0; width: 28px; height: 28px; background: #0f172a;
      border: 1px solid #334155; border-radius: 8px; font-size: 12px;
      font-weight: 700; color: #6366f1; display: flex; align-items: center; justify-content: center;
    }}
    .card-title {{ font-size: 16px; font-weight: 700; color: #f1f5f9; line-height: 1.4; }}
    .badge {{
      display: inline-block; font-size: 11px; font-weight: 600;
      padding: 3px 10px; border-radius: 20px; margin-bottom: 12px; color: #fff;
    }}
    .meta-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }}
    .meta-chip {{
      font-size: 11px; color: #64748b; background: #0f172a;
      border: 1px solid #1e293b; padding: 3px 10px; border-radius: 20px;
    }}
    .meta-chip strong {{ color: #94a3b8; }}
    .summary {{ font-size: 14px; color: #94a3b8; line-height: 1.75; margin-bottom: 16px; }}
    .card-footer {{
      display: flex; align-items: center; justify-content: flex-end;
      padding-top: 14px; border-top: 1px solid #334155;
    }}
    .read-btn {{
      display: inline-block; font-size: 12px; font-weight: 600; color: #6366f1;
      text-decoration: none; padding: 6px 16px; border: 1px solid #6366f1;
      border-radius: 8px; transition: all 0.2s;
    }}
    .read-btn:hover {{ background: #6366f1; color: #fff; }}

    /* ── 빈 결과 ── */
    .empty-state {{ text-align: center; padding: 60px 20px; color: #475569; }}
    .empty-state .icon {{ font-size: 48px; margin-bottom: 16px; }}

    /* ── 아카이브 ── */
    .archive-table {{ width: 100%; border-collapse: collapse; }}
    .archive-table th, .archive-table td {{
      padding: 12px 16px; text-align: left;
      border-bottom: 1px solid #1e293b; font-size: 14px;
    }}
    .archive-table th {{ color: #64748b; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
    .archive-table td a {{ color: #6366f1; text-decoration: none; }}
    .archive-table td a:hover {{ text-decoration: underline; }}

    footer {{ text-align: center; font-size: 12px; color: #334155; padding: 24px; border-top: 1px solid #1e293b; }}

    @media (max-width: 680px) {{
      .layout {{ flex-direction: column; }}
      .sidebar {{ width: 100%; position: static; }}
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
    {date_nav}
  </header>

  <div class="layout">
    <aside class="sidebar">{sidebar}</aside>
    <main id="card-list">{body}</main>
  </div>

  <footer>자동 수집 · OpenAI 큐레이션 · DAI Guild</footer>

  <script>
    // ── 필터 & 정렬 로직 ──
    let activeCategory = 'all';
    let activeSort = 'score-desc';  // 기본: 관련도 높은 순

    function applyFilter() {{
      const cards = document.querySelectorAll('.card');
      cards.forEach(card => {{
        const cat = card.dataset.category;
        const hidden = activeCategory !== 'all' && cat !== activeCategory;
        card.setAttribute('data-hidden', hidden ? 'true' : 'false');
      }});
    }}

    function applySort() {{
      const list = document.getElementById('card-list');
      const cards = Array.from(list.querySelectorAll('.card'));
      cards.sort((a, b) => {{
        if (activeSort === 'score-desc') return Number(b.dataset.score) - Number(a.dataset.score);
        if (activeSort === 'score-asc')  return Number(a.dataset.score) - Number(b.dataset.score);
        if (activeSort === 'date-desc')  return b.dataset.date.localeCompare(a.dataset.date);
        if (activeSort === 'date-asc')   return a.dataset.date.localeCompare(b.dataset.date);
        return 0;
      }});
      cards.forEach(c => list.appendChild(c));
    }}

    function setCategory(cat, el) {{
      activeCategory = cat;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      el.classList.add('active');
      applyFilter();
    }}

    function setSort(sort, el) {{
      activeSort = sort;
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      el.classList.add('active');
      applySort();
    }}
  </script>
</body>
</html>"""


def _format_pub_date(published_at: str) -> str:
    if not published_at:
        return ""
    try:
        dt = datetime.fromisoformat(published_at).astimezone(KST)
        return dt.strftime("%Y.%m.%d %H:%M KST")
    except Exception:
        return published_at[:10]


def _card_html(article: dict, index: int) -> str:
    category  = article.get("category", "기타")
    color     = CATEGORY_COLOR.get(category, "#6b7280")
    emoji     = CATEGORY_EMOJI.get(category, "📌")
    region    = "🇰🇷" if article.get("region") == "domestic" else "🌐"
    score     = article.get("score", 0)
    title     = article["title"].replace("<", "&lt;").replace(">", "&gt;")
    summary   = article.get("summary_ko", "").replace("<", "&lt;").replace(">", "&gt;")
    source    = article.get("source", "")
    pub_str   = _format_pub_date(article.get("published_at", ""))
    pub_raw   = article.get("published_at", "")[:19]  # 정렬용

    return f"""
    <div class="card" data-category="{category}" data-score="{score}" data-date="{pub_raw}">
      <div class="card-header">
        <div class="card-number">{index}</div>
        <div class="card-title">{title}</div>
      </div>
      <span class="badge" style="background:{color}">{emoji} {category}</span>
      <div class="meta-row">
        <span class="meta-chip">{region} <strong>{source}</strong></span>
        {"<span class='meta-chip'>🗓 <strong>" + pub_str + "</strong></span>" if pub_str else ""}
        <span class="meta-chip">관련도 <strong>{score}점</strong></span>
      </div>
      <p class="summary">{summary}</p>
      <div class="card-footer">
        <a class="read-btn" href="{article['link']}" target="_blank" rel="noopener">원문 보기 →</a>
      </div>
    </div>"""


def _sidebar_html(articles: list[dict]) -> str:
    from collections import Counter
    cat_counts = Counter(a.get("category", "기타") for a in articles)

    filter_items = '<button class="filter-btn active" onclick="setCategory(\'all\', this)"><span class="dot" style="background:#6366f1"></span>전체 <span class="count">' + str(len(articles)) + '</span></button>\n'
    for cat, color in CATEGORY_COLOR.items():
        if cat_counts.get(cat, 0) > 0:
            filter_items += f'<button class="filter-btn" onclick="setCategory(\'{cat}\', this)"><span class="dot" style="background:{color}"></span>{cat} <span class="count">{cat_counts[cat]}</span></button>\n'

    return f"""
    <div class="sidebar-section">
      <div class="sidebar-title">카테고리</div>
      {filter_items}
    </div>
    <div class="sidebar-section">
      <div class="sidebar-title">정렬</div>
      <button class="sort-btn active" onclick="setSort('score-desc', this)">🏆 관련도 높은 순</button>
      <button class="sort-btn" onclick="setSort('score-asc', this)">📉 관련도 낮은 순</button>
      <button class="sort-btn" onclick="setSort('date-desc', this)">🕐 최신순</button>
      <button class="sort-btn" onclick="setSort('date-asc', this)">🕰 오래된 순</button>
    </div>"""


def _daily_body(data: dict) -> tuple[str, str]:
    """(sidebar_html, body_html) 반환"""
    date_str = data["date"]
    articles = data.get("articles", [])
    try:
        dt = datetime.fromisoformat(date_str)
        date_ko = dt.strftime("%Y년 %m월 %d일")
    except Exception:
        date_ko = date_str

    header = f"""
    <div style="margin-bottom:24px;">
      <h2 style="font-size:20px;font-weight:700;color:#f1f5f9;">📰 {date_ko} 뉴스</h2>
      <p style="font-size:13px;color:#64748b;margin-top:4px;">총 {len(articles)}개 선별</p>
    </div>"""

    if not articles:
        body = header + """
    <div class="empty-state">
      <div class="icon">🔍</div>
      <p>오늘은 기준에 맞는 뉴스를 찾지 못했습니다.<br>내일 다시 확인해주세요.</p>
    </div>"""
        sidebar = _sidebar_html([])
        return sidebar, body

    cards = "\n".join(_card_html(a, i + 1) for i, a in enumerate(articles))
    return _sidebar_html(articles), header + cards


def _get_sorted_dates() -> list:
    """archive/index.json에서 날짜 목록을 정렬해서 반환"""
    if not ARCHIVE_INDEX.exists():
        return []
    with open(ARCHIVE_INDEX, "r", encoding="utf-8") as f:
        index = json.load(f)
    return sorted([e["date"] for e in index.get("entries", [])], reverse=True)


def _date_nav_html(date_str: str, all_dates: list) -> str:
    """이전/현재/다음 날짜 네비게이션 HTML"""
    if not all_dates:
        return ""
    # all_dates는 최신순 정렬 → index 0이 가장 최신
    try:
        idx = all_dates.index(date_str)
    except ValueError:
        return ""

    prev_date = all_dates[idx + 1] if idx + 1 < len(all_dates) else None  # 이전(오래된)
    next_date = all_dates[idx - 1] if idx - 1 >= 0 else None              # 다음(최신)

    prev_html = f'<a href="{prev_date}.html">← {prev_date}</a>' if prev_date else '<span class="disabled">← 이전</span>'
    next_html = f'<a href="{next_date}.html">{next_date} →</a>' if next_date else '<span class="disabled">다음 →</span>'
    current_html = f'<span class="current">📅 {date_str}</span>'

    return f'<div class="date-nav">{prev_html}{current_html}{next_html}</div>'


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

    all_dates = _get_sorted_dates()
    date_nav = _date_nav_html(date_str, all_dates)
    sidebar, body = _daily_body(data)
    page = _base_html(f"DAI 길드 뉴스 — {date_ko}", sidebar, body, date_nav)

    (DOCS_DIR / "index.html").write_text(page, encoding="utf-8")
    print(f"  생성: docs/index.html")

    (DOCS_DIR / f"{date_str}.html").write_text(page, encoding="utf-8")
    print(f"  생성: docs/{date_str}.html")

    _update_archive_page()


def _update_archive_page():
    if not ARCHIVE_INDEX.exists():
        return

    with open(ARCHIVE_INDEX, "r", encoding="utf-8") as f:
        index = json.load(f)

    entries = index.get("entries", [])
    rows = "".join(
        f'<tr><td><a href="{e["date"]}.html">{e["date"]}</a></td>'
        f'<td>{e.get("count", 0)}개</td></tr>\n'
        for e in entries
    )

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

    sidebar = """
    <div class="sidebar-section">
      <div class="sidebar-title">정렬</div>
      <button class="sort-btn active" onclick="setSort('date-desc', this)">🕐 최신순</button>
      <button class="sort-btn" onclick="setSort('date-asc', this)">🕰 오래된 순</button>
    </div>"""

    (DOCS_DIR / "archive.html").write_text(
        _base_html("DAI 길드 뉴스 아카이브", sidebar, body), encoding="utf-8"
    )
    print(f"  생성: docs/archive.html")
