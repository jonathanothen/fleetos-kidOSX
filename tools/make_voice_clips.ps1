# Makes all voice clips listed in docs/content/voice-lines.csv with ElevenLabs (Swedish).
# The API key is read from the ELEVENLABS_API_KEY environment variable and is never written to disk.
#   powershell -File tools\make_voice_clips.ps1 -Out C:\temp\voice-draft [-Only snd_,num_007] [-Force]
param(
  [string]$Csv = "$PSScriptRoot\..\docs\content\voice-lines.csv",
  [string]$Out = "$PSScriptRoot\..\voice-draft\sv",
  [string]$VoiceId = '4Ct5uMEndw4cJ7q0Jx0l',          # Elin - Neutral and Clear (sv-SE)
  [string]$Model = 'eleven_turbo_v2_5',
  [string[]]$Only = @(),                                # id prefixes to (re)make
  [switch]$Force)
if (-not $env:ELEVENLABS_API_KEY) { throw 'Set ELEVENLABS_API_KEY first' }
New-Item -ItemType Directory -Force $Out | Out-Null
# What the voice should say for a letter SOUND (not the name): a held sound, then the example word.
$sound = @{ a='Aaa'; b='Bbb'; c='Sss'; d='Ddd'; e='Eee'; f='Fff'; g='Ggg'; h='Hhh'; i='Iii'; j='Jjj'; k='Kkk'; l='Lll'; m='Mmm';
            n='Nnn'; o='Ooo'; p='Ppp'; r='Rrr'; s='Sss'; t='Ttt'; u='Uuu'; v='Vvv'; x='Ksss'; y='Yyy'; z='Zzz';
            aa='Ååå'; ae='Äää'; oe='Ööö' }
# Swedish pronunciation of the example word where the spelling misleads (z and x sound like s)
$say = @{ zebra='sebra'; xylofon='sylofon'; cykel='sykel' }
$rows = Import-Csv -Path $Csv -Encoding UTF8
$log = @(); $n = 0
foreach ($r in $rows) {
  if ($Only.Count -gt 0 -and -not ($Only | Where-Object { $r.id.StartsWith($_) })) { continue }
  $text = $r.text
  $speed = 1.0; $prev = ''
  switch ($r.type) {
    'letter_sound' { $key = $r.id.Substring(4); $w = $r.text; if ($say.ContainsKey($w)) { $w = $say[$w] }
                      $text = "$($sound[$key]). <break time=""0.6s""/> $($w.Substring(0,1).ToUpper() + $w.Substring(1))."; $speed = 0.85; $prev = 'Vi pratar svenska. Ordet är: ' }
    'word'         { $prev = 'Vi pratar svenska. Ordet är: ' }
    'letter_name'  { $prev = 'Bokstaven heter ' }
    'phrase'       { $speed = 0.8 }   # whole sentences came out too fast at 1.0; single words were fine
  }
  $file = Join-Path $Out "$($r.id).mp3"
  if ((Test-Path $file) -and -not $Force) { continue }
  $body = @{ text = $text; model_id = $Model; language_code = 'sv'; seed = 42
             voice_settings = @{ stability = 0.65; similarity_boost = 0.75; speed = $speed } }
  if ($prev) { $body.previous_text = $prev }
  $body = $body | ConvertTo-Json -Compress -Depth 4
  for ($try = 1; $try -le 3; $try++) {
    try {
      Invoke-WebRequest -Uri "https://api.elevenlabs.io/v1/text-to-speech/$VoiceId`?output_format=mp3_44100_64" -Method Post `
        -Headers @{ 'xi-api-key' = $env:ELEVENLABS_API_KEY } -ContentType 'application/json; charset=utf-8' `
        -Body ([Text.Encoding]::UTF8.GetBytes($body)) -OutFile $file -ErrorAction Stop
      $n++; $log += "$($r.id),$text"; break
    } catch {
      if ($try -eq 3) { "FAILED $($r.id): $($_.ErrorDetails.Message)" } else { Start-Sleep -Seconds (2 * $try) }
    }
  }
}
$log | Set-Content -Path (Join-Path $Out '_spoken-texts.csv') -Encoding UTF8
"made $n clips in $Out"