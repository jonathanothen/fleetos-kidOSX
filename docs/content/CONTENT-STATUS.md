# Röstklipp: status och kända brister (utkast v0.1)

Klippen i `rootfs/overlay/usr/share/kidsos/games/assets/voices/sv/` är gjorda med ElevenLabs (rösten *Elin –
Neutral and Clear*, svenska) av `tools/make_voice_clips.ps1` och godkända som **tillräckligt bra för nu**. De ska
förbättras senare. Format: mp3, mono, 44,1 kHz, 64 kbit/s (inte Ogg och inte ljudnivåjämnade, se CONTENT-ORDER.md).

Så gjordes de (för att kunna göras om): modell `eleven_turbo_v2_5`, `language_code=sv`, `seed=42`, stabilitet 0,65.
- fraser: fart 0,8; siffror och ord: fart 1,0 (ord med svensk kontext före sig, osynlig för lyssnaren);
- bokstavsljud: "Mmm. (0,6 s paus) M som i mus." fart 0,85; c och z sägs som S, zebra stavas "sebra", cykel "sykel";
- bokstavsnamn: "Bokstaven B." (K: "Kå."); frasen före säger då bara "Kan du hitta" / "Tryck på".

## Att åtgärda senare
- Lyssna igenom alla 257 klipp; ange felaktiga id:n och gör om dem med `-Only <id> -Force`.
- Slutna konsonantljud (b, d, g, k, p, t) kan få en extra vokal; ev. mänsklig inspelning.
- Bokstavsnamn h, j, q, w, x, z är inte särskilt kontrollerade.
- Tiotalen (`num_030`–`num_090`) och korta ord (`wrd_ko`, `wrd_ur`, `wrd_oe`) kan vara för korta.
- Ljudnivå och format: normalisera till −18 LUFS och ev. konvertera till Ogg när `ffmpeg` finns.
- Licens: kontrollera att rösten får användas kommersiellt i den planerade produkten.
- Byt ElevenLabs-API-nyckeln (den har klistrats in i en chatt).
## Bilder (utkast v0.1)

De 62 bilderna i `rootfs/overlay/usr/share/kidsos/games/assets/images/` (`img_<ord>.svg`) kom som en zip från användaren och är
en första version: platt stil, mjuk kontur, 6–8 färger, 256 × 256, 30 KB totalt. Kontrollerat: alla 62 id:n finns och inga
är extra, giltig XML, inga gradienter, filter, text eller skript. De ska göras fantasifullare senare.

Kända svagheter att åtgärda: `ko` ser ut som en katt, `hund` och `mus` liknar varandra, `banan` är bara en halvmåne,
`bro`, `mat` och `sjö` är abstrakta, `tak` är svårt att känna igen. Bilderna är ritade på transparent bakgrund.
