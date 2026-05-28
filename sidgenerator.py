#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sidgenerator.py
===============
Bygger en snygg, fristående HTML-sida (index.html) av alla aktuella
upphandlingar. Sidan är helt självständig – inga externa beroenden utöver
ett par webbtypsnitt – och kan publiceras gratis via GitHub Pages.

Anropas från bevakning.py med den fullständiga listan av (normaliserade)
upphandlingar – alltså ALLA aktiva, inte bara de nya.
"""

import html
from datetime import datetime, timezone


def _esc(s):
    return html.escape(str(s)) if s else ""


def _fmt_date(s):
    """Försöker visa datum snyggt; faller tillbaka på råtext."""
    if not s:
        return ""
    raw = str(s)
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw[:len(fmt) + 2], fmt).strftime("%-d %b %Y")
        except (ValueError, TypeError):
            continue
    return raw[:10]


def _country_label(code):
    mapping = {
        "SWE": "Sverige", "SE": "Sverige",
        "NOR": "Norge", "NO": "Norge",
        "DNK": "Danmark", "DK": "Danmark",
        "FIN": "Finland", "FI": "Finland",
        "ISL": "Island", "IS": "Island",
    }
    c = (code or "").upper().strip()
    return mapping.get(c, code or "")


def _card(it, is_new):
    badge = '<span class="badge badge--new">Ny</span>' if is_new else ""
    deadline = _fmt_date(it.get("deadline"))
    deadline_html = (
        f'<div class="meta__item"><span class="meta__label">Sista anbudsdag</span>'
        f'<span class="meta__value meta__value--deadline">{_esc(deadline)}</span></div>'
        if deadline else ""
    )
    buyer_html = (
        f'<div class="meta__item"><span class="meta__label">Köpare</span>'
        f'<span class="meta__value">{_esc(it.get("buyer"))}</span></div>'
        if it.get("buyer") else ""
    )
    country = _country_label(it.get("country"))
    country_html = (
        f'<div class="meta__item"><span class="meta__label">Land</span>'
        f'<span class="meta__value">{_esc(country)}</span></div>'
        if country else ""
    )
    cpv_html = (
        f'<div class="meta__item"><span class="meta__label">CPV</span>'
        f'<span class="meta__value meta__value--mono">{_esc(it.get("cpv"))}</span></div>'
        if it.get("cpv") else ""
    )
    link = _esc(it.get("link"))
    link_html = (
        f'<a class="card__link" href="{link}" target="_blank" rel="noopener">'
        f'Läs hela annonsen <span aria-hidden="true">→</span></a>'
        if link else ""
    )

    return f"""
        <article class="card{' card--new' if is_new else ''}" data-country="{_esc((it.get('country') or '').upper())}">
          <header class="card__head">
            {badge}
            <h2 class="card__title">{_esc(it.get('title'))}</h2>
          </header>
          <div class="meta">
            {buyer_html}
            {country_html}
            {deadline_html}
            {cpv_html}
          </div>
          {link_html}
        </article>"""


def render_page(items, new_ids, cfg=None):
    """items: lista av normaliserade dicts. new_ids: set av id som är nya."""
    cfg = cfg or {}
    title = cfg.get("site_title", "Upphandlingsbevakning")
    subtitle = cfg.get("site_subtitle", "Aktuella upphandlingar inom inredning, arkitektur och design – Norden")

    updated = datetime.now(timezone.utc).strftime("%-d %B %Y, %H:%M UTC")
    total = len(items)
    new_count = sum(1 for it in items if it.get("id") in new_ids)

    # Nya överst, sedan efter deadline (tomma deadlines sist).
    def sort_key(it):
        is_new = 0 if it.get("id") in new_ids else 1
        dl = it.get("deadline") or "9999-99-99"
        return (is_new, dl)

    items_sorted = sorted(items, key=sort_key)
    cards = "\n".join(_card(it, it.get("id") in new_ids) for it in items_sorted)

    if not items_sorted:
        cards = """
        <div class="empty">
          <p>Inga aktiva upphandlingar matchar bevakningen just nu.</p>
          <p class="empty__sub">Det är normalt i en smal nisch – kom tillbaka imorgon.</p>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{_esc(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Spline+Sans+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink: #16130f;
    --paper: #f4efe6;
    --paper-2: #ece5d8;
    --card: #fbf8f1;
    --accent: #b5471f;        /* terrakotta */
    --accent-soft: #d98a5a;
    --line: #d8cfc0;
    --muted: #6b6256;
    --new: #2f6d4f;           /* skogsgrön för "Ny" */
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    background: var(--paper);
    color: var(--ink);
    font-family: "Newsreader", Georgia, serif;
    font-size: 18px;
    line-height: 1.5;
    background-image:
      radial-gradient(circle at 12% -10%, rgba(181,71,31,0.06), transparent 40%),
      radial-gradient(circle at 100% 0%, rgba(47,109,79,0.05), transparent 35%);
    min-height: 100vh;
  }}

  .wrap {{ max-width: 1080px; margin: 0 auto; padding: 0 28px; }}

  /* ---- Header ---- */
  header.site {{
    padding: 64px 0 36px;
    border-bottom: 2px solid var(--ink);
    margin-bottom: 4px;
  }}
  .eyebrow {{
    font-family: "Spline Sans Mono", monospace;
    font-size: 12px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 18px;
  }}
  h1.site-title {{
    font-family: "Fraunces", serif;
    font-weight: 600;
    font-size: clamp(38px, 7vw, 76px);
    line-height: 0.98;
    letter-spacing: -0.02em;
    max-width: 14ch;
  }}
  .subtitle {{
    font-family: "Newsreader", serif;
    font-style: italic;
    font-size: clamp(18px, 2.4vw, 23px);
    color: var(--muted);
    margin-top: 18px;
    max-width: 46ch;
  }}

  /* ---- Stat / status rad ---- */
  .statusbar {{
    display: flex;
    flex-wrap: wrap;
    gap: 14px 36px;
    align-items: baseline;
    padding: 22px 0 30px;
    font-family: "Spline Sans Mono", monospace;
    font-size: 13px;
    letter-spacing: 0.04em;
    color: var(--muted);
    border-bottom: 1px solid var(--line);
    margin-bottom: 40px;
  }}
  .statusbar strong {{ color: var(--ink); font-weight: 500; }}
  .statusbar .dot {{ color: var(--accent); }}

  /* ---- Filterknappar ---- */
  .filters {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 36px; }}
  .filter {{
    font-family: "Spline Sans Mono", monospace;
    font-size: 12px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 7px 15px;
    border: 1px solid var(--line);
    background: transparent;
    color: var(--muted);
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.18s ease;
  }}
  .filter:hover {{ border-color: var(--ink); color: var(--ink); }}
  .filter.is-active {{ background: var(--ink); color: var(--paper); border-color: var(--ink); }}

  /* ---- Kort ---- */
  .grid {{ display: grid; gap: 2px; background: var(--line); border: 1px solid var(--line); }}
  @media (min-width: 720px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}

  .card {{
    background: var(--card);
    padding: 30px 30px 26px;
    display: flex;
    flex-direction: column;
    position: relative;
    transition: background 0.2s ease, transform 0.2s ease;
    animation: rise 0.5s ease backwards;
  }}
  .card:hover {{ background: #fff; }}
  .card--new {{ background: linear-gradient(180deg, rgba(47,109,79,0.07), var(--card) 60%); }}

  .card__head {{ margin-bottom: 18px; }}
  .badge {{
    display: inline-block;
    font-family: "Spline Sans Mono", monospace;
    font-size: 10px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 4px;
    margin-bottom: 12px;
  }}
  .badge--new {{ background: var(--new); color: #fff; }}
  .card__title {{
    font-family: "Fraunces", serif;
    font-weight: 500;
    font-size: 24px;
    line-height: 1.15;
    letter-spacing: -0.01em;
  }}

  .meta {{ display: grid; gap: 12px; margin-bottom: 22px; margin-top: auto; }}
  .meta__item {{ display: flex; flex-direction: column; gap: 2px; }}
  .meta__label {{
    font-family: "Spline Sans Mono", monospace;
    font-size: 10.5px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent);
  }}
  .meta__value {{ font-size: 16.5px; line-height: 1.35; }}
  .meta__value--deadline {{ font-weight: 500; }}
  .meta__value--mono {{ font-family: "Spline Sans Mono", monospace; font-size: 13px; color: var(--muted); }}

  .card__link {{
    font-family: "Spline Sans Mono", monospace;
    font-size: 13px;
    letter-spacing: 0.03em;
    color: var(--accent);
    text-decoration: none;
    border-top: 1px solid var(--line);
    padding-top: 16px;
    display: inline-flex;
    gap: 8px;
    align-items: center;
    transition: gap 0.18s ease, color 0.18s ease;
  }}
  .card__link:hover {{ color: var(--ink); gap: 14px; }}

  .empty {{ grid-column: 1 / -1; background: var(--card); padding: 80px 30px; text-align: center; }}
  .empty p {{ font-family: "Fraunces", serif; font-size: 22px; }}
  .empty__sub {{ font-style: italic; color: var(--muted); font-size: 17px !important; margin-top: 8px; font-family: "Newsreader", serif !important; }}

  /* ---- Footer ---- */
  footer.site {{
    margin-top: 56px;
    padding: 30px 0 70px;
    border-top: 1px solid var(--line);
    font-family: "Spline Sans Mono", monospace;
    font-size: 12px;
    letter-spacing: 0.04em;
    color: var(--muted);
    line-height: 1.7;
  }}
  footer.site a {{ color: var(--accent); text-decoration: none; }}
  footer.site a:hover {{ text-decoration: underline; }}

  @keyframes rise {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
  .card:nth-child(1) {{ animation-delay: 0.02s; }}
  .card:nth-child(2) {{ animation-delay: 0.06s; }}
  .card:nth-child(3) {{ animation-delay: 0.10s; }}
  .card:nth-child(4) {{ animation-delay: 0.14s; }}
  .card:nth-child(5) {{ animation-delay: 0.18s; }}
  .card:nth-child(6) {{ animation-delay: 0.22s; }}

  @media (prefers-reduced-motion: reduce) {{ .card {{ animation: none; }} }}
</style>
</head>
<body>
  <div class="wrap">
    <header class="site">
      <div class="eyebrow">Egen bevakning · uppdateras automatiskt</div>
      <h1 class="site-title">{_esc(title)}</h1>
      <p class="subtitle">{_esc(subtitle)}</p>
    </header>

    <div class="statusbar">
      <span><span class="dot">●</span> Senast uppdaterad <strong>{_esc(updated)}</strong></span>
      <span><strong>{total}</strong> aktiva upphandlingar</span>
      <span><strong>{new_count}</strong> nya sedan föregående körning</span>
      <span>Källa: <strong>TED · ted.europa.eu</strong></span>
    </div>

    <div class="filters" id="filters">
      <button class="filter is-active" data-filter="ALL">Alla</button>
      <button class="filter" data-filter="SWE">Sverige</button>
      <button class="filter" data-filter="NOR">Norge</button>
      <button class="filter" data-filter="DNK">Danmark</button>
      <button class="filter" data-filter="FIN">Finland</button>
    </div>

    <main class="grid" id="grid">
{cards}
    </main>

    <footer class="site">
      Bygger på TED (Tenders Electronic Daily), EU:s officiella upphandlingsdatabas, och visar
      upphandlingar över EU:s tröskelvärden. Mindre upphandlingar under tröskeln annonseras endast
      nationellt (e-Avrop, Kommers m.fl.) och syns inte här.<br>
      Genererad automatiskt · <a href="https://ted.europa.eu" target="_blank" rel="noopener">ted.europa.eu</a>
    </footer>
  </div>

  <script>
    // Enkel landsfiltrering – ren JS, inga beroenden.
    const filters = document.querySelectorAll('.filter');
    const cards = document.querySelectorAll('.card');
    filters.forEach(btn => btn.addEventListener('click', () => {{
      filters.forEach(b => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      const f = btn.dataset.filter;
      cards.forEach(c => {{
        const country = (c.dataset.country || '');
        const match = f === 'ALL'
          || country === f
          || (f === 'SWE' && country === 'SE')
          || (f === 'NOR' && country === 'NO')
          || (f === 'DNK' && country === 'DK')
          || (f === 'FIN' && country === 'FI');
        c.style.display = match ? '' : 'none';
      }});
    }}));
  </script>
</body>
</html>"""
