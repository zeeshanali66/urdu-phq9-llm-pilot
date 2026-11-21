# Overnight runner: wait for all models, run judges with the temperature watchdog, build results, then shut down.
$ErrorActionPreference = "Continue"
$proj = "F:\Masters\mini-project"
$ollama = "F:\Masters\tools\Ollama\ollama.exe"
$log = "$proj\results\run.log"
New-Item -ItemType Directory -Force "$proj\results" | Out-Null
function Log($m) { "$(Get-Date -Format 'HH:mm:ss')  $m" | Out-File -Append -Encoding utf8 $log }

Log "waiting for all models"
while (-not ((& $ollama list) -match "gemma3:12b")) { Start-Sleep -Seconds 60 }
Log "models ready, starting judges"

$p = Start-Process -FilePath "python" -ArgumentList "-I", "$proj\pipeline.py", "judge" -WorkingDirectory $proj `
     -RedirectStandardOutput "$proj\results\judge.log" -RedirectStandardError "$proj\results\judge.err" -WindowStyle Hidden -PassThru
Start-Process -FilePath "python" -ArgumentList "-I", "$proj\watchdog.py", $p.Id -WorkingDirectory $proj -WindowStyle Hidden
$p.WaitForExit()
Log "judges finished (exit $($p.ExitCode))"

& python -I "$proj\pipeline.py" results *> "$proj\results\results.log"
Log "results built"

shutdown /a 2>$null          # cancel the 8 AM backup timer
shutdown /s /t 300 /c "Research run finished. Shutting down in 5 minutes."
Log "shutdown scheduled in 5 minutes"
