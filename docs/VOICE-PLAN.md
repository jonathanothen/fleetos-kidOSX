# Plan: fler röster med ElevenLabs

Mål: barnen ska aldrig behöva läsa för att förstå vad de ska göra. Idag har vi 257 klipp (siffror 0–100, bokstavsnamn,
bokstavsljud, 62 ord och ett fåtal fraser). Det som saknas är **meningar** (instruktioner), **mer variation i beröm**
och **klockans språk** ("kvart i fyra"). Alla nya rader är redan tillagda i
[`docs/content/voice-lines.csv`](content/voice-lines.csv) (59 st, typ `phrase`, tillsammans ca 900 tecken) och spelen har
koden som spelar dem. **Tills klippen är gjorda hoppas de över tyst**, så ingenting går sönder.

## 1. Vad som beställs (59 klipp)

| Grupp | id-prefix | Exempel | Används i |
|---|---|---|---|
| Klockan, instruktion | `say_what_time` | "Vad är klockan?" | Klockan |
| Klockan, tid uttalad | `say_clock_*` (12 st) | "Klockan är" + "halv" + *fyra* | Klockan, efter rätt svar |
| Mattelek, meningar | `say_pick_*`, `say_count_*`, `say_how_many_*`, `say_write_answer` | "Hur många är kvar?" | Mattelek (fas 2, se nedan) |
| Para ihop, Lyssna | `say_tap_word`, `say_drag_word`, `say_tap_picture`, `say_listen`, `say_point_right` | "Dra ordet till bilden" | Para ihop, Lyssna och peka |
| Minne | `say_find_pairs`, `say_turn_card`, `say_pair_found`, `say_not_pair` | "Du hittade ett par!" | Minne |
| Mönster, Rita | `say_what_next`, `say_continue_pattern`, `say_draw_something`, `say_saved`, `say_new_picture_q` | "Vad kommer sen?" | Mönster, Rita |
| Beröm och uppmuntran | `say_correct_5`–`8`, `say_retry_3`–`4`, `say_hint_look`, `say_encourage_*` | "Vad duktig du är!" | alla spel (slumpas bland de som finns) |
| Startskärmen | `say_home_hello`, `tile_*` (11 st) | "Räkna", "Para ihop" | startskärmen (fas 3) |
| Framsteg och pauser | `say_new_level`, `say_level_up`, `say_rest_eyes` | "Nu blir det lite svårare!" | framsteg, pausregel (fas 3) |

Klockan läses som en svensk gör: 3:30 = "halv fyra", 3:45 = "kvart i fyra", 3:25 = "fem i halv fyra". Spelet sätter
ihop klippen ("Klockan är" + "kvart i" + *fyra*) med siffrorna som redan finns. Från 25 minuter över används nästa timme.

## 2. Hur klippen görs (inget nytt verktyg behövs)

Skriptet `tools/make_voice_clips.ps1` gör **bara de klipp som saknas** (befintliga filer rörs inte utan `-Force`) och
använder rösten Elin med samma inställningar som förut (fraser: hastighet 0,8).

1. **Rotera nyckeln först.** Den gamla nyckeln har klistrats in i en chatt och ska anses förbrukad: skapa en ny i
   ElevenLabs (Profile → API keys) och ta bort den gamla.
2. Sätt nyckeln bara i det aktuella PowerShell-fönstret (den sparas aldrig i någon fil):
   ```powershell
   $env:ELEVENLABS_API_KEY = '<den nya nyckeln>'
   ```
3. Gör alla nya klipp direkt in i spelens ljudmapp:
   ```powershell
   powershell -File tools\make_voice_clips.ps1 -Out rootfs\overlay\usr\share\kidsos\games\assets\voices\sv -Only say_,tile_
   ```
   (`-Only` tar prefix. Provar du först några: `-Only say_clock_,say_what_`.)
4. Kör kontrollen: `python3 tests/validate_content.py` (ska säga att inget längre är "pending").

Kostnad: ca 900 tecken ≈ en bråkdel av en månads kvot på planen vi har.

## 3. Lyssna igenom innan det går vidare (tidigare erfarenhet)

Förra omgången hittade lyssningen fel som ingen kontroll kan hitta. Kolla särskilt:

- **Korta ord:** "halv", "i", "fem i", "tio i" kan bli för korta eller svälja ljud. Fungerar de inte som egna klipp
  görs hela fraser ("tio i fyra") för just de tiderna i stället för att sätta ihop.
- **Tempo:** meningar låter för snabba vid hastighet 1,0, därför 0,8.
- **"Klockan är" + tal:** hör att det flyter ihop, annars läggs en kort paus (`<break time="0.3s"/>`) i det första klippet.
- **Beröm:** de åtta varianterna ska låta olika glada men lugna, ingen ska låta ironisk.
- Skriv avvikelser i `docs/content/CONTENT-STATUS.md` med id, vad som lät fel och hur det rättades.

## 4. Fas för fas

1. **Fas 1, nu:** klockan, Minne, Mönster, Rita, Para ihop, beröm. Allt är redan inkopplat, det räcker att göra klippen.
2. **Fas 2:** byt ut de ensamma orden i Mattelek ("fler", "färre") mot hela meningar och lägg till "Räkna de streckade".
   *Görs först när klippen finns*, annars blir spelet tystare än idag. Ändring: `generators.py` (`more`) och en rad i
   `mattelek/main.py`.
3. **Fas 3:** startskärmen läser upp rutans namn när man trycker ("Räkna …") och hälsar. Kräver att startskärmen
   (GTK) spelar ljud; lösningen är `pw-play` på samma mp3-filer. Samtidigt: röst när en ny nivå nås och vilopåminnelse
   efter ca 20 minuters spel.
4. **Fas 4, senare:** fler språk (engelska först). Då dubbleras listan; idén är att `voices/<språk>/` redan är
   uppbyggd så (`sv`), och spelen har språkvalet i `Voice(lang)`.

## 5. Öppna frågor

- **Licens:** kontrollera att ElevenLabs-planen tillåter att klippen följer med en bild som lämnas vidare till andra
  (skolor, andra barn). Samma punkt som i `docs/content/CONTENT-STATUS.md`.
- **Volym:** klippen är inte loudness-normaliserade. Om volymen skiljer sig mellan klippen: installera ffmpeg
  (`winget install Gyan.FFmpeg`) och normalisera alla till samma nivå.
- **Barnets namn:** ett uppläst "Hej <namn>!" går inte att generera i förväg. Alternativ är en mänsklig inspelning eller
  att generera klippet vid installationen. Utanför den här planen tills vidare.
