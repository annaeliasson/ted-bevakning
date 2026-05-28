# Kom igång – steg för steg (ingen kodning krävs)

Den här guiden tar dig från noll till en egen webbsida som listar dina
upphandlingar och uppdaterar sig själv varje vardagsmorgon. Du behöver inte
kunna programmera. Räkna med 20–30 minuter första gången.

Allt är gratis. Du behöver bara ett GitHub-konto.

---

## Vad du kommer ha när du är klar

En webbadress som ser ut ungefär så här:

> `https://DITTANVÄNDARNAMN.github.io/upphandlingar/`

Du går in på den när du vill och ser en snygg lista över alla aktuella
upphandlingar. Den uppdateras automatiskt – du behöver aldrig göra något mer.

---

## Steg 1 – Skapa ett GitHub-konto (om du inte har ett)

1. Gå till **https://github.com** och klicka **Sign up**.
2. Följ instruktionerna (e-post, lösenord, användarnamn). Anteckna ditt
   **användarnamn** – det blir en del av din webbadress.
3. Verifiera din e-post.

> GitHub är en gratis tjänst där man lägger upp och "hostar" kod och filer.
> Din instinkt stämde helt.

---

## Steg 2 – Lägg upp projektet på GitHub

Du ska skapa ett nytt "repository" (förkortas "repo" – tänk en projektmapp)
och ladda upp filerna jag gav dig.

1. När du är inloggad, klicka på **+** uppe till höger → **New repository**.
2. **Repository name:** skriv `upphandlingar` (eller vad du vill – det blir
   en del av webbadressen).
3. Välj **Public**. (Pages-publicering kräver Public på gratiskontot.)
   - Vill du absolut ha det privat: det går, men kräver betald GitHub-plan
     för Pages. För det här ändamålet är Public helt okej – det finns inget
     hemligt på sidan, bara offentliga upphandlingar.
4. Klicka **Create repository**.
5. På nästa sida, klicka länken **uploading an existing file**
   (står i texten "…or upload an existing file").
6. **Packa först upp** zip-filen `ted-bevakning.zip` på din dator.
   Dra sedan in **alla filerna** (inklusive den dolda `.github`-mappen) i
   webbläsarrutan. Om `.github`-mappen inte följer med: se rutan längst ned.
7. Längst ner, klicka den gröna knappen **Commit changes**.

> "Commit" betyder ungefär "spara och bekräfta". Du kommer se ordet ofta –
> det betyder bara "spara den här ändringen".

---

## Steg 3 – Slå på automatiken (GitHub Actions)

Filerna innehåller redan ett färdigt schema. Du behöver bara aktivera det.

1. I ditt repo, klicka fliken **Actions** högst upp.
2. Om GitHub frågar om du vill aktivera workflows: klicka
   **I understand my workflows, go ahead and enable them** (grön knapp).

Klart. Den kör automatiskt varje vardag kl 07:00 UTC. Du kan också starta en
testkörning direkt – se steg 5.

---

## Steg 4 – Slå på webbsidan (GitHub Pages)

1. I repot, klicka fliken **Settings** (kugghjulet).
2. I vänstermenyn, klicka **Pages**.
3. Under **Build and deployment → Source**, välj **GitHub Actions** i
   rullgardinsmenyn. (Inte "Deploy from a branch".)
4. Det är allt – ingen knapp att trycka. Adressen visas här uppe efter
   första körningen.

---

## Steg 5 – Kör första gången (för att testa direkt)

Du behöver inte vänta till imorgon bitti.

1. Gå till fliken **Actions**.
2. Klicka på **TED-bevakning** i vänsterlistan.
3. Klicka knappen **Run workflow** till höger → **Run workflow** igen.
4. Vänta ~1–2 minuter. En grön bock betyder att det gick bra.
5. Gå tillbaka till **Settings → Pages**. Nu står din webbadress där.
   Klicka på den – din lista är live!

> Första körningen mejlar inte (för att inte skicka hela historiken på en
> gång). Den fyller bara sidan och "minnet". Från och med nästa körning
> mejlas bara det som är nytt – om du slår på e-post, se nedan.

---

## (Valfritt) Steg 6 – Slå på mejlnotiser också

Sidan funkar utan detta. Men vill du även få ett mejl när något nytt dyker upp:

1. I repot: **Settings → Secrets and variables → Actions**.
2. Klicka **New repository secret**.
   - **Name:** `TED_SMTP_PASSWORD`
   - **Secret:** ditt e-post-app-lösenord (för Gmail: skapa ett under
     Google-konto → Säkerhet → App-lösenord). **Inte** ditt vanliga lösenord.
   - Klicka **Add secret**.
3. Öppna filen `config.yaml` i repot (klicka på den → pennikonen för att
   redigera), ändra under `email:`:
   ```yaml
   email:
     enabled: true
     from: din-avsändaradress@gmail.com
     to:
       - upphandling@itg.studio
   ```
4. Klicka **Commit changes**.

---

## Hur du ändrar vad som bevakas

Vill du lägga till ett sökord eller en CPV-kod, eller byta rubrik på sidan?

1. Öppna **config.yaml** i repot.
2. Klicka pennikonen (Edit).
3. Ändra det du vill (allt är kommenterat på svenska).
4. **Commit changes**. Nästa körning använder de nya inställningarna.

Du behöver alltså aldrig röra själva koden – bara den här inställningsfilen.

---

## Om något strular

- **Ingen webbadress dök upp?** Kontrollera att du i Steg 4 valde
  *GitHub Actions* som source, och att körningen i Actions fick grön bock.
- **Röd bock i Actions?** Klicka på körningen för att se felet. Vanligast är
  att `config.yaml` fått ett litet stavfel – jämför med originalet.
- **Sidan är tom?** Det kan helt enkelt betyda att inga upphandlingar matchar
  just nu. Prova att i `config.yaml` tillfälligt ta bort några `keywords`
  eller lägga till fler länder, och kör igen.
- **`.github`-mappen följde inte med vid uppladdning?** Den är "dold" på
  vissa datorer. Enklaste lösningen: i repot, klicka **Add file → Create new
  file**, skriv i namnrutan exakt:
  `.github/workflows/bevakning.yml` (snedstrecken skapar mapparna åt dig),
  och klistra in innehållet från filen med samma namn. Commit.

---

## Vad det här kostar

Ingenting. GitHub-konto, GitHub Actions (för publika repo) och GitHub Pages
är gratis. TED:s API är gratis och kräver ingen nyckel. Det finns ingen
kreditmätare som med Lovable – sidan kan uppdatera sig hur ofta som helst utan
kostnad.
