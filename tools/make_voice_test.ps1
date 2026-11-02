# Makes a few Swedish test clips with ElevenLabs. The API key is read from the ELEVENLABS_API_KEY environment
# variable and is never written to disk.   Usage: powershell -File make_voice_test.ps1 -Out C:\temp\voice-test
param([string]$Out = "$PSScriptRoot\..\voice-test")
if (-not $env:ELEVENLABS_API_KEY) { throw "Set ELEVENLABS_API_KEY first" }
New-Item -ItemType Directory -Force $Out | Out-Null
$voices = [ordered]@{ alice = 'Xb7hH8MSUJpSbSDYk0k2'; matilda = 'XrExE9yKIg1WjnnlVkGX'; jessica = 'cgSgspJ2msm6clMCkdW9' }
$clips  = [ordered]@{ snd_s = 'Sss. Sol.'; snd_m = 'Mmm. Mus.'; snd_a = 'Aaa. Apa.'; snd_r = 'Rrr. Ros.'; num_007 = 'sju'; say_correct_2 = 'Bra jobbat!' }
foreach ($v in $voices.Keys) {
  foreach ($c in $clips.Keys) {
    $body = @{ text = $clips[$c]; model_id = 'eleven_multilingual_v2'; voice_settings = @{ stability = 0.6; similarity_boost = 0.75 } } | ConvertTo-Json -Compress
    $file = Join-Path $Out "$v-$c.mp3"
    Invoke-WebRequest -Uri "https://api.elevenlabs.io/v1/text-to-speech/$($voices[$v])?output_format=mp3_44100_128" -Method Post `
      -Headers @{ 'xi-api-key' = $env:ELEVENLABS_API_KEY } -ContentType 'application/json; charset=utf-8' `
      -Body ([Text.Encoding]::UTF8.GetBytes($body)) -OutFile $file
    "{0}  {1:N0} KB" -f $file, ((Get-Item $file).Length / 1KB)
  }
}