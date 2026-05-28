#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TED API syntax-diagnos – provar flera syntaxer och rapporterar vilken som funkar."""
import json, sys, urllib.error, urllib.request

ENDPOINT = "https://api.ted.europa.eu/v3/notices/search"

CANDIDATES = [
    ("A: FT= med citattecken + CY=", 'FT="inredningsarkitekt" AND CY=SWE'),
    ("B: FT= + CY med hakparentes", 'FT="inredningsarkitekt" AND CY=[SWE]'),
    ("C: ren text + CY hakparentes", 'inredningsarkitekt AND CY=[SWE]'),
    ("D: FT~ med parentes (tilde)", 'FT~(inredningsarkitekt) AND CY=[SWE]'),
    ("E: bara FT, inget land", 'FT="inredningsarkitekt"'),
    ("F: place-of-performance SE", 'FT="inredningsarkitekt" AND place-of-performance=SE'),
    ("G: country-buyer alias", 'FT="inredningsarkitekt" AND country-buyer=SWE'),
    ("H: ren text utan fält", 'inredningsarkitekt'),
    ("I: classification-cpv=", 'classification-cpv=71220000'),
    ("J: flera värden i parentes", 'FT=(inredningsarkitekt OR arkitekt) AND CY=[SWE]'),
]
FIELDS = ["publication-number", "notice-title", "buyer-country"]

def try_query(query):
    payload = {"query": query, "fields": FIELDS, "limit": 5, "scope": "ACTIVE",
               "checkQuerySyntax": False, "paginationMode": "ITERATION"}
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        total = (data.get("totalNoticeCount") or data.get("total")
                 or len(data.get("notices") or data.get("results") or []))
        results = data.get("notices") or data.get("results") or []
        sample = ""
        if results:
            t = results[0].get("notice-title") or results[0].get("TI") or ""
            if isinstance(t, dict): t = next(iter(t.values()), "")
            if isinstance(t, list): t = t[0] if t else ""
            sample = str(t)[:80]
        return ("OK", total, sample, sorted(data.keys()))
    except urllib.error.HTTPError as e:
        return ("HTTP %d" % e.code, e.read().decode("utf-8","ignore")[:200].replace("\n"," "), "", "")
    except Exception as e:
        return ("ERR", f"{type(e).__name__}: {str(e)[:150]}", "", "")

def main():
    print("="*70); print("TED API SYNTAX-DIAGNOS"); print("Endpoint:", ENDPOINT); print("="*70)
    winners = []
    for desc, q in CANDIDATES:
        print(f"\n--- {desc}"); print(f"    query: {q}")
        status, a, b, keys = try_query(q)
        if status == "OK":
            print(f"    OK | totalNoticeCount={a}")
            if b: print(f"       exempel: {b}")
            if keys: print(f"       nycklar: {keys}")
            try:
                if int(a) > 0: winners.append((desc, q, a))
            except (ValueError, TypeError): pass
        else:
            print(f"    MISSLYCKADES: {status} | {a}")
    print("\n" + "="*70)
    if winners:
        print(f"VINNARE ({len(winners)} gav traffar):")
        for desc, q, total in winners:
            print(f"  - {desc}  ->  {total} traffar"); print(f"      {q}")
    else:
        print("INGEN syntax gav traffar. Klistra in HELA loggen till Claude.")
    print("="*70)

if __name__ == "__main__":
    main()
