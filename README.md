# TED-bevakning (Nivå 2)

Ett litet, eget bevakningssystem för offentliga upphandlingar i Norden.
Hämtar nya upphandlingar från **TED** (EU:s officiella databas, [ted.europa.eu](https://ted.europa.eu)),
filtrerar på **CPV-koder OCH fritext**, kommer ihåg vad du redan sett och
mejlar dig bara det som är nytt.

Fritextfiltret är poängen: det fångar upphandlingar som ligger under "fel"
eller för bred CPV-kod – samma sak som dyra tjänster som Tendium tar betalt för,
fast gratis och under din egen kontroll.

> **Obs om täckning:** TED innehåller alla upphandlingar **över EU:s
> tröskelvärden**. Mindre upphandlingar under tröskeln annonseras bara
> nationellt (e-Avrop, Kommers, Mercell osv.). Det här systemet ersätter
> alltså inte dina gratisbevakningar på de portalerna – det kompletterar dem
> och täcker hela Norden på ett ställe. För de riktigt stora ramavtalen
> (regioner, universitet, statliga fastighetsägare) är TED ofta primärkällan.

---

## Vad du får

| Fil | Vad den gör |
|-----|-------------|
| `bevakning.py` | Själva skriptet |
| `sidgenerator.py` | Bygger den snygga webbsidan (index.html) |
| `config.yaml` | All konfiguration – CPV-koder, fritext, länder, sidrubrik, e-post |
| `requirements.txt` | Python-beroende (bara pyyaml) |
| `.github/workflows/bevakning.yml` | Kör automatiskt OCH publicerar sidan, gratis |
| `KOMIGÅNG.md` | **Börja här** – steg-för-steg-guide utan förkunskaper |
| `index.html` | Skapas automatiskt – din webbsida |
| `seen.json` | Skapas automatiskt – minns vad du redan sett |

> **Kan inte koda / aldrig använt GitHub?** Öppna **`KOMIGÅNG.md`** – den tar
> dig genom allt på ren svenska, klick för klick, utan förkunskaper.

---

## Snabbstart (testa lokalt på 5 minuter)

Kräver Python 3.9+.

```bash
pip install -r requirements.txt
python bevakning.py
```

Första gången är `email.enabled: false` i config, så rapporten skrivs i
terminalen istället för att mejlas. Då ser du direkt vad bevakningen hittar.

---

## Konfigurera (config.yaml)

Allt du normalt ändrar finns där, med kommentarer:

- **cpv_codes** – era nuvarande koder ligger redan inne, plus de bredare
  paraplykoderna jag föreslog. Kommentera bort det ni inte vill ha.
- **keywords** – fritextord som matchas mot titel + beskrivning.
- **countries** – `SWE NOR DNK FIN` förifyllt (3-bokstavskoder).
- **email** – sätt `enabled: true` när du vill ha mejl.

---

## Slå på e-post

1. Sätt i `config.yaml`:
   ```yaml
   email:
     enabled: true
     from: din-avsändaradress@gmail.com
     to:
       - upphandling@itg.studio
   ```
2. **Lösenordet ligger ALDRIG i filen.** Det läses från miljövariabeln
   `TED_SMTP_PASSWORD`. För Gmail: skapa ett *app-lösenord*
   (Google-konto → Säkerhet → Tvåstegsverifiering → App-lösenord) och kör:
   ```bash
   export TED_SMTP_PASSWORD="ditt-app-lösenord"
   python bevakning.py
   ```
3. Använder du annan mejl än Gmail – ändra `smtp_host` / `smtp_port`.

> Säkerhetsnot: ett app-lösenord ger åtkomst till mejlutskick. Skapa gärna en
> separat avsändaradress för bevakningen istället för ditt privata konto.

---

## Kör automatiskt och gratis (GitHub Actions)

Du slipper egen server. Workflow-filen kör skriptet varje vardagsmorgon.

1. Lägg upp mappen som ett **privat** GitHub-repo.
2. I repot: **Settings → Secrets and variables → Actions → New repository secret**
   - Namn: `TED_SMTP_PASSWORD`
   - Värde: ditt app-lösenord
3. Sätt `email.enabled: true` i `config.yaml` och pusha.
4. Klart. Du kan starta en testkörning manuellt under fliken **Actions**.

`seen.json` committas tillbaka automatiskt efter varje körning så att du
aldrig får samma upphandling dubbelt.

---

## Hur query:n fungerar

Skriptet bygger en TED *expert query* enligt mönstret:

```
( classification-cpv IN (dina CPV-koder)
  OR  notice-title ~ ("dina nyckelord")
  OR  description-proc ~ ("dina nyckelord") )
AND place-of-performance IN (SWE NOR DNK FIN)
```

Bara **aktiva** (öppna) upphandlingar hämtas (`scope: ACTIVE`).
TED:s Search API kräver **ingen API-nyckel** för datakonsumenter.

---

## Vidareutveckling till Nivå 3 (AI-filtrering)

När/om bruset blir för stort: skicka varje ny upphandlings titel +
beskrivning till en språkmodell med frågan *"relevant för en
inredningsarkitektbyrå som gör X? ja/nej + kort motivering"* och filtrera på
svaret innan mejlet skickas. Det blir en liten kostnad per upphandling i
API-avgift, men försumbart jämfört med ett abonnemang. Funktionen
`build_report()` är den naturliga platsen att haka in det.

---

## Felsökning

- **Inga träffar alls?** Testa att tillfälligt tömma `keywords` och bara köra
  på CPV, eller bredda `countries`. Kontrollera utskriften av query:n överst.
- **`HTTP 400 / syntax`?** Något nyckelord kan innehålla tecken som krockar
  med query-språket – ta bort specialtecken.
- **Fältnamn ändras hos TED?** Skriptet normaliserar defensivt och bygger
  länkar från `publication-number` om `links` saknas. Om TED gör större
  ändringar: jämför `REQUEST_FIELDS` mot aktuell dokumentation på
  https://docs.ted.europa.eu/api/latest/search.html
