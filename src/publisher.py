"""
GitHub Pages 퍼블리셔
- index.html: 최근 7일치 한 페이지, 최신 날짜 펼침 / 과거 날짜 토글
- 사이드바: 카테고리 필터 + 정렬
- 더 오래된 날짜는 아카이브 페이지에서 확인
"""

RECENT_DAYS = 7  # 홈에 표시할 최근 일수

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter

KST = timezone(timedelta(hours=9))
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "docs"
DAILY_DIR = BASE_DIR / "data" / "daily"
ARCHIVE_INDEX = BASE_DIR / "data" / "archive" / "index.json"

CATEGORY_COLOR = {
    "AI도구활용":    "#6366f1",
    "데이터분석+AI": "#0ea5e9",
    "LLM응용":      "#8b5cf6",
    "생산성":       "#10b981",
    "AI트렌드":     "#f59e0b",
    "기타":         "#6b7280",
}
CATEGORY_EMOJI = {
    "AI도구활용":    "🛠️",
    "데이터분석+AI": "📊",
    "LLM응용":      "🤖",
    "생산성":       "⚡",
    "AI트렌드":     "📡",
    "기타":         "📌",
}


# ── 공통 HTML 껍데기 ──────────────────────────────────────────────
def _base_html(title: str, sidebar: str, body: str) -> str:
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

    /* ── 레이아웃 ── */
    .layout {{
      display: flex; max-width: 1140px; margin: 0 auto;
      padding: 32px 20px 80px; gap: 28px; align-items: flex-start;
    }}

    /* ── 사이드바 ── */
    .sidebar {{
      width: 220px; flex-shrink: 0; position: sticky; top: 24px;
    }}
    .sidebar-section {{
      background: #1e293b; border: 1px solid #334155;
      border-radius: 14px; padding: 18px; margin-bottom: 16px;
    }}
    .sidebar-title {{
      font-size: 11px; font-weight: 600; color: #64748b;
      text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px;
    }}
    .filter-btn {{
      display: flex; align-items: center; gap: 8px;
      width: 100%; padding: 7px 10px; margin-bottom: 3px;
      background: transparent; border: 1px solid transparent;
      border-radius: 8px; color: #94a3b8; font-size: 13px;
      cursor: pointer; text-align: left; transition: all 0.15s;
    }}
    .filter-btn:hover {{ background: #0f172a; border-color: #334155; color: #e2e8f0; }}
    .filter-btn.active {{ background: #0f172a; border-color: #6366f1; color: #e2e8f0; }}
    .filter-btn .dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
    .filter-btn .count {{
      margin-left: auto; font-size: 11px; color: #475569;
      background: #0f172a; padding: 1px 7px; border-radius: 10px;
    }}
    .sort-btn {{
      display: flex; align-items: center; gap: 6px;
      width: 100%; padding: 7px 10px; margin-bottom: 3px;
      background: transparent; border: 1px solid transparent;
      border-radius: 8px; color: #94a3b8; font-size: 13px;
      cursor: pointer; text-align: left; transition: all 0.15s;
    }}
    .sort-btn:hover {{ background: #0f172a; border-color: #334155; color: #e2e8f0; }}
    .sort-btn.active {{ background: #0f172a; border-color: #6366f1; color: #e2e8f0; }}

    /* ── 메인 ── */
    main {{ flex: 1; min-width: 0; }}

    /* ── 날짜 섹션 (토글 컨테이너) ── */
    .date-section {{ margin-bottom: 28px; }}
    .date-section[data-date-hidden="true"] {{ display: none; }}

    .date-toggle {{
      display: flex; align-items: center; gap: 10px;
      width: 100%; background: transparent; border: none;
      cursor: pointer; padding: 0; margin-bottom: 16px; text-align: left;
    }}
    .date-toggle .date-label {{
      font-size: 17px; font-weight: 700; color: #f1f5f9;
    }}
    .date-toggle .date-chip {{
      font-size: 11px; color: #64748b; background: #1e293b;
      border: 1px solid #334155; padding: 2px 10px; border-radius: 20px;
    }}
    .date-toggle .date-chip.today {{
      color: #6366f1; border-color: #6366f1; background: rgba(99,102,241,0.1);
    }}
    .date-toggle .toggle-icon {{
      margin-left: auto; font-size: 13px; color: #475569;
      transition: transform 0.2s;
    }}
    .date-toggle.collapsed .toggle-icon {{ transform: rotate(-90deg); }}

    .date-divider {{
      height: 1px; background: #1e293b; margin-bottom: 16px;
    }}

    .date-cards {{ }}
    .date-cards.collapsed {{ display: none; }}

    /* ── 카드 ── */
    .card {{
      background: #1e293b; border: 1px solid #334155; border-radius: 14px;
      padding: 24px; margin-bottom: 16px; transition: border-color 0.2s, transform 0.15s;
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
    .empty-state {{ text-align: center; padding: 40px 20px; color: #475569; }}
    .empty-state .icon {{ font-size: 40px; margin-bottom: 12px; }}

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

    @media (max-width: 700px) {{
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
      <a href="index.html">홈</a>
      <a href="archive.html">아카이브</a>
    </nav>
  </header>

  <div class="layout">
    <aside class="sidebar">{sidebar}</aside>
    <main>{body}</main>
  </div>

  <footer>자동 수집 · OpenAI 큐레이션 · DAI Guild</footer>

  <script>
    let activeCategory = 'all';
    let activeSort = 'score-desc';

    // ── 카테고리 필터 ──
    function setCategory(cat, el) {{
      activeCategory = cat;
      document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
      el.classList.add('active');
      applyFilters();
    }}

    // ── 정렬 ──
    function setSort(sort, el) {{
      activeSort = sort;
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      el.classList.add('active');
      applySort();
    }}

    function applyFilters() {{
      document.querySelectorAll('.card').forEach(card => {{
        const catMatch = activeCategory === 'all' || card.dataset.category === activeCategory;
        card.setAttribute('data-hidden', catMatch ? 'false' : 'true');
      }});
    }}

    function applySort() {{
      document.querySelectorAll('.date-cards').forEach(container => {{
        const cards = Array.from(container.querySelectorAll('.card'));
        cards.sort((a, b) => {{
          if (activeSort === 'score-desc') return Number(b.dataset.score) - Number(a.dataset.score);
          if (activeSort === 'score-asc')  return Number(a.dataset.score) - Number(b.dataset.score);
          if (activeSort === 'date-desc')  return b.dataset.date.localeCompare(a.dataset.date);
          if (activeSort === 'date-asc')   return a.dataset.date.localeCompare(b.dataset.date);
          return 0;
        }});
        cards.forEach(c => container.appendChild(c));
      }});
    }}

    // ── 날짜 토글 ──
    function toggleDate(dateStr) {{
      const btn = document.querySelector(`.date-toggle[data-date="${{dateStr}}"]`);
      const cards = document.getElementById('cards-' + dateStr);
      if (!btn || !cards) return;
      const isCollapsed = cards.classList.contains('collapsed');
      if (isCollapsed) {{
        cards.classList.remove('collapsed');
        btn.classList.remove('collapsed');
      }} else {{
        cards.classList.add('collapsed');
        btn.classList.add('collapsed');
      }}
    }}
  </script>
</body>
</html>"""


# ── 유틸 ──────────────────────────────────────────────────────────
def _format_pub_date(published_at: str) -> str:
    if not published_at:
        return ""
    try:
        dt = datetime.fromisoformat(published_at).astimezone(KST)
        return dt.strftime("%Y.%m.%d %H:%M KST")
    except Exception:
        return published_at[:10]


def _get_sorted_dates() -> list:
    if not ARCHIVE_INDEX.exists():
        return []
    with open(ARCHIVE_INDEX, "r", encoding="utf-8") as f:
        index = json.load(f)
    return sorted([e["date"] for e in index.get("entries", [])], reverse=True)


def _load_all_articles(dates: list) -> list:
    """최근 RECENT_DAYS일치 기사를 [{date, articles}] 형태로 반환"""
    result = []
    for d in dates[:RECENT_DAYS]:
        path = DAILY_DIR / f"{d}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            result.append({"date": d, "articles": data.get("articles", [])})
    return result


# ── 카드 HTML ────────────────────────────────────────────────────
def _card_html(article: dict, index: int) -> str:
    category = article.get("category", "기타")
    color    = CATEGORY_COLOR.get(category, "#6b7280")
    emoji    = CATEGORY_EMOJI.get(category, "📌")
    region   = "🇰🇷" if article.get("region") == "domestic" else "🌐"
    score    = article.get("score", 0)
    title    = article["title"].replace("<", "&lt;").replace(">", "&gt;")
    summary  = article.get("summary_ko", "").replace("<", "&lt;").replace(">", "&gt;")
    source   = article.get("source", "")
    pub_str  = _format_pub_date(article.get("published_at", ""))
    pub_raw  = article.get("published_at", "")[:19]

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


# ── 사이드바 ─────────────────────────────────────────────────────
def _sidebar_html(all_data: list) -> str:
    # 카테고리 카운트 (최근 RECENT_DAYS일 기준)
    all_articles = [a for entry in all_data for a in entry["articles"]]
    cat_counts = Counter(a.get("category", "기타") for a in all_articles)
    total = len(all_articles)

    cat_items = f'<button class="filter-btn cat-btn active" onclick="setCategory(\'all\', this)"><span class="dot" style="background:#6366f1"></span>전체 <span class="count">{total}</span></button>\n'
    for cat, color in CATEGORY_COLOR.items():
        if cat_counts.get(cat, 0) > 0:
            cat_items += f'<button class="filter-btn cat-btn" onclick="setCategory(\'{cat}\', this)"><span class="dot" style="background:{color}"></span>{cat} <span class="count">{cat_counts[cat]}</span></button>\n'

    return f"""
    <div class="sidebar-section">
      <div class="sidebar-title">카테고리</div>
      {cat_items}
    </div>
    <div class="sidebar-section">
      <div class="sidebar-title">정렬</div>
      <button class="sort-btn active" onclick="setSort('score-desc', this)">🏆 관련도 높은 순</button>
      <button class="sort-btn" onclick="setSort('score-asc', this)">📉 관련도 낮은 순</button>
      <button class="sort-btn" onclick="setSort('date-desc', this)">🕐 최신순</button>
      <button class="sort-btn" onclick="setSort('date-asc', this)">🕰 오래된 순</button>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-title">더보기</div>
      <a href="archive.html" style="display:flex;align-items:center;gap:8px;padding:8px 10px;color:#94a3b8;font-size:13px;text-decoration:none;border-radius:8px;transition:all 0.15s;" onmouseover="this.style.background='#0f172a';this.style.color='#e2e8f0'" onmouseout="this.style.background='';this.style.color='#94a3b8'">📂 전체 아카이브 →</a>
    </div>"""


# ── 메인 본문 (날짜별 토글 섹션) ────────────────────────────────
def _main_body(all_data: list) -> str:
    today = datetime.now(KST).strftime("%Y-%m-%d")
    sections = []

    for entry in all_data:
        date_str = entry["date"]
        articles = entry["articles"]
        is_today = date_str == today

        try:
            dt = datetime.fromisoformat(date_str)
            date_ko = dt.strftime("%Y년 %m월 %d일")
        except Exception:
            date_ko = date_str

        chip = '<span class="date-chip today">오늘</span>' if is_today else f'<span class="date-chip">{len(articles)}개 선별</span>'
        toggle_class = "" if is_today else " collapsed"
        cards_class = "date-cards" if is_today else "date-cards collapsed"

        if not articles:
            cards_html = """
            <div class="empty-state">
              <div class="icon">🔍</div>
              <p>기준에 맞는 뉴스를 찾지 못했습니다.</p>
            </div>"""
        else:
            cards_html = "\n".join(_card_html(a, i + 1) for i, a in enumerate(articles))

        sections.append(f"""
    <div class="date-section" data-date="{date_str}">
      <button class="date-toggle{toggle_class}" data-date="{date_str}" onclick="toggleDate('{date_str}')">
        <span class="date-label">📅 {date_ko}</span>
        {chip}
        <span class="toggle-icon">▼</span>
      </button>
      <div class="date-divider"></div>
      <div class="{cards_class}" id="cards-{date_str}">
        {cards_html}
      </div>
    </div>""")

    return "\n".join(sections)


# ── 진입점 ───────────────────────────────────────────────────────
def publish(date_str: str = None):
    """모든 날짜 데이터를 읽어 index.html 하나로 통합 생성"""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    all_dates = _get_sorted_dates()
    all_data = _load_all_articles(all_dates)

    sidebar = _sidebar_html(all_data)
    body = _main_body(all_data)
    page = _base_html("DAI 길드 뉴스 — 데이터 분석 AI", sidebar, body)

    (DOCS_DIR / "index.html").write_text(page, encoding="utf-8")
    print(f"  생성: docs/index.html ({len(all_dates)}개 날짜)")

    _update_archive_page()


def _update_archive_page():
    if not ARCHIVE_INDEX.exists():
        return

    with open(ARCHIVE_INDEX, "r", encoding="utf-8") as f:
        index = json.load(f)

    entries = index.get("entries", [])

    # 전체 기사 로드 (카테고리 통계용)
    all_articles = []
    for e in entries:
        path = DAILY_DIR / f"{e['date']}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_articles.extend(data.get("articles", []))

    # 카테고리별 통계
    cat_counts = Counter(a.get("category", "기타") for a in all_articles)
    total = len(all_articles)

    # 날짜별 카테고리 분포 계산
    date_cat_map = {}
    for e in entries:
        path = DAILY_DIR / f"{e['date']}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cats = Counter(a.get("category", "기타") for a in data.get("articles", []))
            date_cat_map[e["date"]] = cats

    # 날짜 테이블 행
    def _cat_badges(date_str):
        cats = date_cat_map.get(date_str, {})
        if not cats:
            return '<span style="color:#475569;font-size:12px;">—</span>'
        badges = ""
        for cat, color in CATEGORY_COLOR.items():
            if cats.get(cat, 0) > 0:
                emoji = CATEGORY_EMOJI.get(cat, "")
                badges += f'<span style="display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;background:{color}22;color:{color};border:1px solid {color}44;margin:2px 2px;">{emoji} {cat} {cats[cat]}</span>'
        return badges

    rows = "".join(
        f'<tr><td style="white-space:nowrap;color:#94a3b8;font-weight:600;">{e["date"]}</td>'
        f'<td style="white-space:nowrap;text-align:center;">{e.get("count", 0)}개</td>'
        f'<td>{_cat_badges(e["date"])}</td></tr>\n'
        for e in entries
    )

    # 카테고리 요약 카드
    cat_summary = ""
    for cat, color in CATEGORY_COLOR.items():
        cnt = cat_counts.get(cat, 0)
        if cnt > 0:
            emoji = CATEGORY_EMOJI.get(cat, "")
            pct = round(cnt / total * 100) if total else 0
            cat_summary += f"""
            <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px 20px;display:flex;align-items:center;gap:12px;">
              <span style="font-size:22px;">{emoji}</span>
              <div style="flex:1;">
                <div style="font-size:13px;font-weight:600;color:#f1f5f9;">{cat}</div>
                <div style="font-size:12px;color:#64748b;margin-top:2px;">{cnt}개 · 전체의 {pct}%</div>
                <div style="height:4px;background:#0f172a;border-radius:2px;margin-top:8px;overflow:hidden;">
                  <div style="height:100%;width:{pct}%;background:{color};border-radius:2px;"></div>
                </div>
              </div>
              <span style="font-size:20px;font-weight:700;color:{color};">{cnt}</span>
            </div>"""

    body = f"""
    <div style="margin-bottom:28px;">
      <h2 style="font-size:20px;font-weight:700;color:#f1f5f9;">📂 전체 아카이브</h2>
      <p style="font-size:13px;color:#64748b;margin-top:4px;">총 {len(entries)}일 · {total}개 기사</p>
    </div>

    <h3 style="font-size:14px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:14px;">카테고리별 분포</h3>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-bottom:36px;">
      {cat_summary}
    </div>

    <h3 style="font-size:14px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:14px;">날짜별 기록</h3>
    <div style="background:#1e293b;border:1px solid #334155;border-radius:14px;overflow:hidden;">
      <table class="archive-table">
        <thead><tr><th>날짜</th><th style="text-align:center;">기사 수</th><th>카테고리</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""

    sidebar = f"""
    <div class="sidebar-section">
      <div class="sidebar-title">전체 통계</div>
      <div style="font-size:13px;color:#94a3b8;padding:4px 0;">📅 {len(entries)}일 수집</div>
      <div style="font-size:13px;color:#94a3b8;padding:4px 0;">📰 총 {total}개 기사</div>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-title">카테고리</div>
      {''.join(f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;font-size:13px;color:#94a3b8;"><span style="width:8px;height:8px;border-radius:50%;background:{CATEGORY_COLOR[cat]};flex-shrink:0;display:inline-block;"></span>{cat}<span style="margin-left:auto;color:#475569;">{cat_counts.get(cat,0)}</span></div>' for cat in CATEGORY_COLOR if cat_counts.get(cat,0)>0)}
    </div>
    <div class="sidebar-section">
      <a href="index.html" style="display:flex;align-items:center;gap:8px;padding:8px 10px;color:#94a3b8;font-size:13px;text-decoration:none;border-radius:8px;transition:all 0.15s;" onmouseover="this.style.color='#e2e8f0'" onmouseout="this.style.color='#94a3b8'">← 홈으로</a>
    </div>"""

    (DOCS_DIR / "archive.html").write_text(
        _base_html("DAI 길드 뉴스 아카이브", sidebar, body), encoding="utf-8"
    )
    print(f"  생성: docs/archive.html")
