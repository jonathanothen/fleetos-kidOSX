# Plan: två egna spel för KidsOS – Mattelek och Skrivlabbet

Status: plan, inget är byggt. Skriven 2026-11-02.

## 0. Utgångspunkter och antaganden

- **Målgrupp:** barn 4–8 år, Samsung XE303C12/XE503C12 (2 GB, två A15-kärnor, ingen användbar GPU-acceleration i
  webbläsaren). Spelen måste därför vara *lätta*: inga ramverk, ingen WebGL, få animationer.
- **"Lära sig skriva spel"** tolkar jag som ett spel där barnen lär sig **skriva**: bokstäver, det egna namnet, ord
  (på tangentbordet, med följ-bokstaven som komplement). Menade du i stället att barnen ska lära sig att *göra egna
  spel* – det täcks redan av Koda (Snap!) och kan bli en tredje punkt med uppdragskort (se avsnitt 6).
- **Teknik (rekommendation):** två fristående webbappar i ren HTML/CSS/JS, öppnade offline i Firefox precis som
  Snap! (`file:///usr/share/kidsos/games/...`). Skäl: samma teknik som redan finns i bilden, ingen byggkedja, går
  att utveckla och testa direkt i Chrome/Edge på Windows, små filer, lätta att ändra. Alternativ: Python + pygame
  (tyngre, svårare att testa på Windows) eller C/SDL (för mycket arbete). Webbfilterpolicyn släpper redan igenom
  `file:///usr/share/kidsos/*`.
- **Spara framsteg:** `localStorage` i barnets Firefox-profil (en profil per barnkonto). Inget lämnar datorn.
- **Hitta först det som redan finns:** bilden innehåller GCompris, TuxMath och Tux Typing. Innan vi bygger: låt ett
  barn prova dem i 1–2 veckor och skriv ner vad som saknas (svensk läroplan, "fyll i räkneexempel", barnets eget
  namn, ingen tidspress). Det som saknas är motiveringen för egna spel.

## 1. Gemensam kärna (`kids-core.js`, görs först)

| Del | Innehåll |
|---|---|
| UI-kit | stora knappar (≥ 96 px), ingen text som barnet måste läsa i första nivåerna, ikoner + röst |
| Ljud | förinspelade korta röstklipp (siffror 0–100, bokstäver, instruktioner), belöningsljud; max ljudnivå följer systemets |
| Lagring | per färdighet: antal rätt/fel, senast sedd, nivå; barnets förnamn från kontot |
| Belöning | samlar klistermärken/djur per avklarad övning, inga poäng som tas bort, inga topplistor |
| Pausregel | efter ca 10–15 min: "Dags för paus!"-skärm (barnet kan välja att fortsätta) |
| Föräldravy | sida `parent.html` med färdighetsöversikt och återställ-knapp (skyddas av en enkel fråga, inte säkerhet) |
| Test | liten testsida som kör alla generatorer och kontrollerar att uppgifter går att lösa |

**Röst:** barn 4–6 kan oftast inte läsa. Förinspelad svensk röst är bäst men måste göras; offline-TTS (t.ex.
espeak-ng) låter robotlikt och måste provas på riktigt. Beslut behövs (se avsnitt 7).

## 2. Mattelek

### 2.1 Pedagogik
- **Läroplan:** mål följer Lgr22 matematik för åk 1–3 (taluppfattning, addition och subtraktion, likhetstecknet och
  enkla ekvationer, multiplikation som upprepad addition, dubbelt/hälften, mönster). *Exakt ordalydelse ska
  kontrolleras mot Skolverkets kursplan* – jag hittade bara förlagens sammanställningar:
  [Favorit matematik, Lgr22-matris](https://www.studentlitteratur.se/globalassets/serier/laromedel/favorit-matematik/favorit_matris_1-3_lgr22_2021.pdf),
  [Skolverkets kursplan (matematik)](https://syllabuswebb.skolverket.se/subject/GRSAMAT01/9/pdf).
- **Konkret → bild → symbol:** varje ny typ av uppgift visas först med föremål (äpplen, prickar), sedan med
  tiorutor/tallinje, sist bara som siffror. Barnet "klättrar" när det klarar det utan stöd.
- **Subitizing och tiorutor:** snabb igenkänning av små mängder (tärningsmönster, tiorutor) är en vanlig del av
  undervisning i taluppfattning. Obs: forskningen visar tydligt samband med matteförmåga men *svagt bevis* för att
  träning i sig ger vinst ([Hechinger Report](https://hechingerreport.org/?p=105260)), och riktlinjerna jag hittade
  bygger mest på läromedel. Därför är det ett inslag bland flera, inte spelets enda motor.
- **Ingen tidspress för de yngsta.** Snabbhet (automatisering av talkombinationer) mäts tyst i bakgrunden för
  7–8-åringar men straffas aldrig.
- **Fel är information:** fel svar ger "Nästan! Prova igen" + ett hjälpsteg (visa föremål → visa tallinje → visa
  svaret och en ny liknande uppgift). Aldrig röd ruta, aldrig minuspoäng.
- **Anpassning:** behärskning styr nivån (t.ex. 8 av 10 rätt utan hjälp på en färdighet → nästa), med lite
  upprepning av äldre färdigheter spridd över tid.

### 2.2 Nivåer (förslag, justeras efter prov med barn)
| Nivå | Ålder | Innehåll |
|---|---|---|
| 0 | 4–5 | räkna föremål 1–10, para ihop mängd och siffra, fler/färre, tärningsmönster |
| 1 | 5–6 | tallinje 0–20, tiorutor, lägga till/ta bort 1–10 med föremål, "hur många fattas till 10?" |
| 2 | 6–7 | addition/subtraktion inom 20, talkamrater till 10, dubblor, +10, `3 + _ = 8`, <, >, = |
| 3 | 7–8 | tal till 100 (tiotal/ental), upprepad addition och rutnät (multiplikation), dubbelt/hälften, enkla textuppgifter, mönster |

### 2.3 Spelloop
- **"Fyll i räkneexemplet":** uppgiften visas med tomma rutor på valfri plats (`4 + 3 = _`, `_ + 3 = 7`, `7 = _ + 3`);
  barnet skriver med tangentbordet eller tryckknappar på skärmen (stora siffror). Det tränar likhetstecknets
  betydelse och inte bara "skriv svaret efter =".
- Ram: en berättelse/miljö per nivå (t.ex. hjälp djuren packa väskor), 10 uppgifter per runda, klistermärke efter runda.
- **Generator:** uppgifter skapas av regler (talområde, operation, saknad plats, representation) med seed, så att de
  går att testa automatiskt och inte upprepas direkt.

## 3. Skrivlabbet (lära sig skriva)

### 3.1 Pedagogik
- **Forskningsläget är blandat:** i studier på förskolebarn lär sig barn kunna *känna igen och skriva bokstäver*
  bättre när de skriver för hand än när de trycker på tangenter ([PubMed 15823243](https://pubmed.ncbi.nlm.nih.gov/15823243),
  [Frontiers in Psychology 2021](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2021.726454/pdf)),
  men en tysk studie fann ingen fördel för handskrift ([sammanfattning](https://boldscience.org/handwriting-versus-typing-for-childrens-literacy/)).
  Studierna är små och gäller korta försök, inte tangentbordsundervisning. **Slutsats för designen:** tangentbordet
  är ett *stöd*, inte en ersättning: spelet innehåller ett läge "Följ bokstaven" (spåra med pekplattan/musen) och
  uppmuntrar förälder/lärare att även låta barnet skriva på papper. Fingerrätt tioformsskrivning är inget mål före
  ~8 år.
- **Personligt:** barnets eget förnamn är första ordet (motiverar mer än "a s d f"). Namnet hämtas från kontot.
- **Ljud–bokstav:** varje bokstav presenteras med ljud + bild + ord ("S som sol"). Ordningen på bokstäverna bör
  stämma med hur barnets skola/förskola gör (många använder ljudande bokstäver först; *ska kontrolleras med en
  lärare*); första förslag: vokaler + vanliga konsonanter, å/ä/ö tidigt eftersom de finns på det svenska
  tangentbordet.
- **Ingen tidspress**, ingen poängjakt. Fel tangent ignoreras vänligt (bokstaven "väntar") eller visas som tips.

### 3.2 Nivåer
| Nivå | Ålder | Innehåll |
|---|---|---|
| A | 4–5 | bokstavsjakt: ljud + bild, hitta tangenten (tangentbordet på skärmen lyser), stora/små bokstäver |
| B | 5–6 | skriv mitt namn (spökbokstäver visar vägen), följ-bokstaven-spårning |
| C | 6–7 | korta ord med bild (sol, hus, katt …), skriv av → skriv efter ljud |
| D | 7–8 | längre ord, ordbilder (vanliga ord), första meningen, versal/punkt, skriv ett eget "brev" med fri text (ingen rättning, bara spara/skriva ut) |

### 3.3 Detaljer att hantera
- Tangentbordslayout: använder systemets (svenska); visa rätt tangenter på bildskärmstangentbordet, hantera `å ä ö`,
  Shift, Caps Lock (stäng av fel läge med vänlig hjälp).
- Barnet kan trycka systemgenvägar (Windows-tangent m.m.): provas; vid behov begränsas i xfce-genvägar för barnkonton.
- Ordlista: ~200 ord i storleksordning, med bilder (egna SVG:er, inga upphovsrättsproblem).

## 4. Filstruktur i repot

```
rootfs/overlay/usr/share/kidsos/games/
  core/kids-core.js, kids-core.css, sounds/, voices/
  mattelek/index.html, game.js, generators.js, levels.json
  skrivlabbet/index.html, game.js, words.json, letters.json
  parent.html
rootfs/overlay/usr/share/applications/kids-math.desktop, kids-write.desktop   (ersätter TuxMath/Tux Typing i menyn om våra är bättre)
tests/  (kör i Node eller webbläsare: generatorer, nivåflöde)
```
Startas med `firefox-esr --new-window file:///usr/share/kidsos/games/mattelek/index.html` (samma mönster som Koda).

## 5. Etapper

| Etapp | Innehåll | Klart när |
|---|---|---|
| E0 | Beslut (avsnitt 7), prova GCompris/TuxMath/Tux Typing med barn, lista brister | beslut och kravlista |
| E1 | `kids-core` + Mattelek nivå 0–1 + skiss av röst/ljud | körs offline på Chromebooken utan hack, <100 MB RAM |
| E2 | Mattelek nivå 2–3, hjälpsteg, lagring, klistermärken | ett barn klarar en 10-minuterspass utan vuxenhjälp |
| E3 | Skrivlabbet A–C (bokstäver, eget namn, ord) + följ-bokstaven | barnets namn kan skrivas, rätt tangent lyser |
| E4 | Skrivlabbet D, föräldravy, pausregel, stresstest av fel tangenter | föräldravyn visar framsteg |
| E5 | Provspelning med 3–5 barn och en lärare, justera nivåer och ljud | ändringslista genomförd |
| E6 | Bygg in i KidsOS (paketera, `.desktop`, README, bygg-test) | bygget går igenom, ikoner i menyn |

## 6. Möjligt tillägg: "Gör ditt eget spel"
Uppdragskort i Koda (Snap!): färdiga startprojekt ("få katten att hoppa", "gör ett gissa-talet-spel") i
`snap/Examples`-stil, 5–10 stycken stegvisa, för 7–8-åringar. Billigt att göra när E1 är klar.

## 7. Beslut och frågor till dig
1. **Tolkning av "skriva":** tangentbord + bokstäver (som här) eller handskrivning/spårning som huvudsak?
2. **Röst:** vem kan spela in svenska röstklipp (~150 korta klipp), eller ska vi prova offline-TTS först?
3. **Språk:** bara svenska från start (rekommenderas) eller fler språk?
4. **Egna spel kontra befintliga:** går vi vidare efter E0 om GCompris/TuxMath räcker för vissa nivåer?
5. **Testbarn/lärare:** finns några 4–8-åringar och en lärare som kan prova i E5?
6. **Läroplan:** ska vi följa Lgr22 åk 1–3 som angivet, och vem bekräftar bokstavsordningen?

## 8. Risker
- Prestanda i Firefox på den här hårdvaran (mäts i E1; håll DOM/CSS enkelt, inga stora bilder).
- Innehåll (röst, bilder, ord) är mer arbete än koden.
- Pedagogiken är underbyggd men inte bevisad för just dessa spel; utvärdera med riktiga barn innan fler funktioner läggs till.
- Fel tangenter/systemgenvägar i skrivspelet kan få barnet ut ur spelet.
