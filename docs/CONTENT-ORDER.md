# Beställning av innehåll: röst, bilder, ljud

Den här filen är **beställningen** till den som producerar innehållet (en annan AI, en frilansare eller du själv med
ElevenLabs). Koden tas fram separat; innehållet måste följa formatet nedan så att det kan läggas in utan handpåläggning.
Beställningslistorna ligger i [content/voice-lines.csv](content/voice-lines.csv) och
[content/words.csv](content/words.csv). Bilder och ljudeffekter anges i avsnitt 3–4.

## 1. Leverans

En enda zip, `kidsos-content-v<N>.zip`, med exakt denna struktur (inga andra filer):

```
kidsos-content/
  manifest.csv                 en rad per levererad fil (se 5)
  README.txt                   verktyg och röst som använts, datum, licenser, kända brister
  voices/sv/<id>.ogg           alla röstklipp
  images/<picture_id>.svg      bilder (en per ord i words.csv)
  sfx/<id>.ogg                 ljudeffekter
```

Allt filnamn är ASCII, gemener, `a-z 0-9 _`. Svenska tecken i id:n är redan omskrivna i listorna (å=aa, ä=ae, ö=oe).
Ändra aldrig ett id; saknas det något, leverera ändå resten och lista bristen i README.txt.

## 2. Röst (`voices/sv/<id>.ogg`)

Antal klipp: se `content/voice-lines.csv` (siffror 0–100, bokstavsnamn, bokstavsljud, ord, instruktioner och
beröm, räkneord som "plus" och "gånger").

| Krav | Värde |
|---|---|
| Språk | svenska (sv-SE), rikssvenska |
| Röst | **en och samma röst** i alla klipp; varm, lugn, tydlig, vuxen, barnvänlig (ingen "skolfröken" som talar nedlåtande) |
| Format | Ogg Vorbis, mono, 22 050 Hz, kvalitet ca q4 (~20–30 KB per klipp) |
| Ljudstyrka | −18 LUFS (±1) integrerat, true peak ≤ −1 dBFS; samma nivå i alla klipp |
| Tystnad | högst 100 ms i början och 250 ms i slutet; inga klick eller andningsljud |
| Längd | siffror/bokstäver/ord 0,3–1,5 s; fraser högst 3 s |
| Innehåll | exakt `text`-kolumnen, inget extra (ingen "okej", inga upprepningar) |
| Betoning | siffror och ord sägs fristående med fallande, avslutande tonfall; frågor har frågande tonfall |
| Siffror | "ett" (inte "en") när det räknas; 21–99 sägs som sammansatta ord (tjugotre) |

**Bokstavsljud (`snd_*`)** säger *ljudet* (t.ex. "sss", inte "ess") följt av ordet ("s … sol"). Det är det svåraste
för talsyntes: beställ först fyra test (`snd_s`, `snd_m`, `snd_a`, `snd_r`) och lyssna innan resten beställs. Fungerar det inte läses dessa av en människa. `snd_q` och `snd_w` finns ej.

**Barnets namn** går inte att förinspelas. Spelet visar namnet i text och säger bara "Hej!".

## 3. Bilder (`images/<picture_id>.svg`)

En bild per rad i `content/words.csv` (`picture_id`). Stil: platt, mjuka rundade former, ljusa färger, tydlig kontur
i en mörk ton, ungefär som övriga KidsOS-ikoner.

| Krav | Värde |
|---|---|
| Format | SVG, `viewBox="0 0 512 512"`, transparent bakgrund |
| Storlek | högst 20 KB per fil |
| Teknik | enbart enkla former och fyllda färger; **inga** gradienter, filter, skuggor, inbäddade bilder eller teckensnitt |
| Färger | högst 8 per bild; kontrast mot både vit och ljusgul bakgrund |
| Text | ingen text i bilden |
| Motiv | ett tydligt föremål, centrerat, fyller 70–90 % av ytan; igenkänningsbart för en 5-åring |
| Rättigheter | egenritat eller genererat med en licens som tillåter fri användning i produkten; inga kända varumärken eller figurer |

## 4. Ljudeffekter (`sfx/<id>.ogg`)

Ogg Vorbis, mono, 22 050 Hz, −20 LUFS, högst 1,5 s, mjuka och glada (inga skarpa eller höga ljud):
`sfx_click`, `sfx_correct`, `sfx_retry` (mjukt, inte "fel"-ljud), `sfx_sticker`, `sfx_round_done`, `sfx_break`,
`sfx_key` (tangent), `sfx_letter_ok`.

## 5. `manifest.csv`

Kolumner: `id,type,file,sha256,bytes,duration_s,tool,notes`. En rad per fil. `type` är `number`, `letter_name`,
`letter_sound`, `word`, `phrase`, `image` eller `sfx`. Filen ska stämma med de levererade filerna.

## 6. Godkännande (görs av oss, inte av leverantören)

Validatorn `tests/validate_content.py` (skrivs i E1) kör mot den uppackade mappen och avvisar leveransen om något av
detta inte stämmer: saknade eller extra id:n, fel format/samplingsfrekvens/kanaler, längd eller ljudnivå utanför
gränserna, SVG med förbjudna element (`linearGradient`, `filter`, `image`, `text`, `script`), filer över storleksgräns,
manifestet stämmer inte (kontrollsumma). Därefter lyssnar en person igenom **alla** klipp och tittar på alla bilder
(en kontaktkarta renderas av validatorn).

## 7. Storlek och kostnad

Ca 260 röstklipp × ~25 KB + 62 bilder × ~10 KB + 8 effekter ≈ 8 MB. Omfattningen växer med nya nivåer; nya id:n
läggs till i listorna och beställs som en ny version (`v2`, `v3` …) utan att ändra gamla id:n.