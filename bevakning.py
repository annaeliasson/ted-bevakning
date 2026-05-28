#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TED-bevakning – Nivå 2
======================
Hämtar nya offentliga upphandlingar från TED (Tenders Electronic Daily),
filtrerar på CPV-koder OCH fritext (för att fånga snett kodade upphandlingar),
håller reda på vad du redan sett, och mejlar dig en sammanställning av nyheterna.

Körs t.ex. en gång per dygn via cron eller GitHub Actions.

Ingen API-nyckel krävs – TED:s Search API v3 är öppen för datakonsumenter.

Konfiguration sker i config.yaml. Se README.md.
"""

import json
import os
import smtplib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Saknar pyyaml. Kör: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

import sidgenerator

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"
SEEN_PATH = BASE_DIR / "seen.json"
PAGE_PATH = BASE_DIR / "index.html"
TED_ENDPOINT = "https://api.ted.europa.eu/v3/notices/search"

# Fält vi ber TED returnera. TED kan returnera vissa fält som listor/objekt
# beroende på notisens språk; koden nedan normaliserar detta defensivt.
REQUEST_FIELDS = [
    "publication-number",
    "notice-title",
    "buyer-name",
    "buyer-country",
    "deadline-receipt-request",
    "publication-date",
    "classification-cpv",
    "place-of-performance",
    "links",
]


# --------------------------------------------------------------------------- #
# Konfiguration
# --------------------------------------------------------------------------- #
def load_config():
    if not CONFIG_PATH.exists():
        print(f"Hittar ingen config: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_query(cfg):
    """Bygger TED:s expert-query-sträng från config.

    Logik:  (CPV-träff  ELLER  fritext-träff)  OCH  land i listan
    Fritextdelen är poängen – den fångar upphandlingar med 'fel' CPV-kod.
    """
    cpv_codes = [str(c).split("-")[0].strip() for c in cfg.get("cpv_codes", [])]
    countries = [c.strip().upper() for c in cfg.get("countries", ["SWE"])]
    keywords = [k.strip() for k in cfg.get("keywords", []) if k.strip()]

    clauses = []

    if cpv_codes:
        cpv_list = " ".join(cpv_codes)
        clauses.append(f"classification-cpv IN ({cpv_list})")

    if keywords:
        # Frasmatchning i titel + beskrivning. Citattecken => exakt fras.
        kw_clauses = []
        for kw in keywords:
            kw_clauses.append(f'notice-title ~ ("{kw}")')
            kw_clauses.append(f'description-proc ~ ("{kw}")')
        clauses.append("(" + " OR ".join(kw_clauses) + ")")

    if not clauses:
        print("Varning: varken CPV-koder eller nyckelord angivna.", file=sys.stderr)
        relevance = "*"
    else:
        relevance = "(" + " OR ".join(clauses) + ")"

    country_clause = ""
    if countries:
        country_clause = " AND place-of-performance IN (" + " ".join(countries) + ")"

    return relevance + country_clause


# --------------------------------------------------------------------------- #
# TED API
# --------------------------------------------------------------------------- #
def fetch_notices(query, max_pages=10, page_limit=100):
    """Hämtar alla notiser som matchar query, med paginering (ITERATION)."""
    all_results = []
    next_token = None

    for _ in range(max_pages):
        payload = {
            "query": query,
            "fields": REQUEST_FIELDS,
            "limit": page_limit,
            "scope": "ACTIVE",            # bara aktiva (öppna) upphandlingar
            "checkQuerySyntax": False,
            "paginationMode": "ITERATION",
        }
        if next_token:
            payload["iterationNextToken"] = next_token

        data = _post(payload)
        if data is None:
            break

        # TED har över tid använt olika nycklar för resultatlistan.
        results = (
            data.get("notices")
            or data.get("results")
            or data.get("noticeList")
            or []
        )
        all_results.extend(results)

        next_token = data.get("iterationNextToken") or data.get("nextToken")
        if not next_token or not results:
            break
        time.sleep(0.5)  # var snäll mot API:et

    return all_results


def _post(payload, retries=3):
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    for attempt in range(retries):
        req = urllib.request.Request(TED_ENDPOINT, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "ignore")[:300]
            print(f"HTTP {e.code} (försök {attempt+1}): {msg}", file=sys.stderr)
            if e.code in (429, 500, 502, 503):
                time.sleep(2 ** attempt)
                continue
            return None
        except Exception as e:
            print(f"Fel (försök {attempt+1}): {type(e).__name__} {e}", file=sys.stderr)
            time.sleep(2 ** attempt)
    return None


# --------------------------------------------------------------------------- #
# Normalisering av notiser (TED-fält är inkonsekventa mellan språk/versioner)
# --------------------------------------------------------------------------- #
def _first_text(value):
    """Plockar ut läsbar text ur fält som kan vara str, list eller dict{språk:text}."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return _first_text(value[0]) if value else ""
    if isinstance(value, dict):
        # föredra svenska/engelska om de finns
        for lang in ("swe", "sv", "eng", "en"):
            if lang in value:
                return _first_text(value[lang])
        # annars första värdet
        for v in value.values():
            return _first_text(v)
    return str(value)


def normalize(notice):
    pub = _first_text(notice.get("publication-number") or notice.get("ND"))
    title = _first_text(notice.get("notice-title") or notice.get("TI"))
    buyer = _first_text(notice.get("buyer-name"))
    country = _first_text(notice.get("buyer-country") or notice.get("place-of-performance"))
    deadline = _first_text(notice.get("deadline-receipt-request"))
    pubdate = _first_text(notice.get("publication-date") or notice.get("PD"))
    cpv = notice.get("classification-cpv")
    if isinstance(cpv, list):
        cpv = ", ".join(_first_text(c) for c in cpv)
    else:
        cpv = _first_text(cpv)

    # Länk: använd links-fältet om det finns, annars bygg från publication-number.
    link = ""
    links = notice.get("links")
    if isinstance(links, dict):
        link = _first_text(links.get("html") or links.get("self") or links)
    elif isinstance(links, str):
        link = links
    if not link and pub:
        # Standardiserad TED-länk: t.ex. 123456-2026 -> .../notice/-/detail/123456-2026
        link = f"https://ted.europa.eu/en/notice/-/detail/{pub}"

    return {
        "id": pub,
        "title": title or "(ingen titel)",
        "buyer": buyer,
        "country": country,
        "deadline": deadline,
        "pubdate": pubdate,
        "cpv": cpv,
        "link": link,
    }


# --------------------------------------------------------------------------- #
# Tillstånd: vad har vi redan sett?
# --------------------------------------------------------------------------- #
def load_seen():
    if SEEN_PATH.exists():
        try:
            with open(SEEN_PATH, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_seen(seen):
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=0)


# --------------------------------------------------------------------------- #
# Rapport / e-post
# --------------------------------------------------------------------------- #
def build_report(new_items):
    lines = []
    lines.append(f"TED-bevakning – {len(new_items)} nya upphandlingar")
    lines.append(f"Körning: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("=" * 60)
    lines.append("")
    for it in new_items:
        lines.append(f"▶ {it['title']}")
        if it["buyer"]:
            lines.append(f"   Köpare:    {it['buyer']}")
        if it["country"]:
            lines.append(f"   Land/ort:  {it['country']}")
        if it["cpv"]:
            lines.append(f"   CPV:       {it['cpv']}")
        if it["deadline"]:
            lines.append(f"   Deadline:  {it['deadline']}")
        if it["pubdate"]:
            lines.append(f"   Publicerad:{it['pubdate']}")
        if it["link"]:
            lines.append(f"   Länk:      {it['link']}")
        lines.append("")
    return "\n".join(lines)


def send_email(cfg, subject, body):
    email_cfg = cfg.get("email") or {}
    if not email_cfg.get("enabled"):
        print("E-post avstängd i config – skriver rapport till stdout istället.\n")
        print(body)
        return

    # Lösenord tas från miljövariabel, ALDRIG från config-filen.
    password = os.environ.get("TED_SMTP_PASSWORD", "")
    if not password:
        print("Saknar TED_SMTP_PASSWORD i miljön – kan inte skicka mejl.", file=sys.stderr)
        print(body)
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = email_cfg["from"]
    msg["To"] = ", ".join(email_cfg["to"])
    msg["Date"] = formatdate(localtime=True)

    host = email_cfg.get("smtp_host", "smtp.gmail.com")
    port = int(email_cfg.get("smtp_port", 587))

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(email_cfg["from"], password)
        server.sendmail(email_cfg["from"], email_cfg["to"], msg.as_string())
    print(f"Mejl skickat till {', '.join(email_cfg['to'])}")


# --------------------------------------------------------------------------- #
# Huvudflöde
# --------------------------------------------------------------------------- #
def main():
    cfg = load_config()
    query = build_query(cfg)
    print(f"Query:\n  {query}\n")

    raw = fetch_notices(
        query,
        max_pages=int(cfg.get("max_pages", 10)),
        page_limit=int(cfg.get("page_limit", 100)),
    )
    print(f"Hämtade {len(raw)} matchande aktiva notiser från TED.")

    notices = [normalize(n) for n in raw]
    notices = [n for n in notices if n["id"]]  # kräver giltigt id

    first_run = not SEEN_PATH.exists()
    seen = load_seen()
    new_ids = {n["id"] for n in notices if n["id"] not in seen}
    new_items = [n for n in notices if n["id"] in new_ids]

    print(f"Varav {len(new_items)} är nya sedan förra körningen.")

    # --- Generera alltid webbsidan (visar ALLA aktiva, nya markerade) ---
    try:
        html_out = sidgenerator.render_page(notices, new_ids, cfg)
        with open(PAGE_PATH, "w", encoding="utf-8") as f:
            f.write(html_out)
        print(f"Skrev webbsida: {PAGE_PATH}")
    except Exception as e:
        print(f"Kunde inte skriva webbsida: {type(e).__name__} {e}", file=sys.stderr)

    # --- Mejla bara om det finns nytt, och inte vid allra första körningen ---
    if first_run:
        print("Första körningen – sparar nuläget utan att mejla hela historiken.")
    elif new_items:
        report = build_report(new_items)
        subject = f"[TED-bevakning] {len(new_items)} nya upphandlingar"
        send_email(cfg, subject, report)
    else:
        print("Inga nya upphandlingar att rapportera.")

    # Uppdatera "sedda" med allt vi just hämtade.
    for n in notices:
        seen.add(n["id"])
    save_seen(seen)


if __name__ == "__main__":
    main()
