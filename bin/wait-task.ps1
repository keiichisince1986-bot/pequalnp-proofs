# Wait until TASKS.md on the claims branch has a task with status todo meant for NAME (or for any).
# Usage, from inside a clone of keiichisince1986-bot/pequalnp-proofs (PowerShell):
#   powershell -ExecutionPolicy Bypass -File bin\wait-task.ps1 -Name Antigravity-Win
# Prints the matching task headers and exits 0. Exits 2 after MaxMinutes (default 25).
param([Parameter(Mandatory=$true)][string]$Name, [int]$MaxMinutes = 25, [int]$Interval = 60)
$end = (Get-Date).AddMinutes($MaxMinutes)
while ($true) {
  git fetch -q origin claims 2>$null
  $text = git show origin/claims:TASKS.md 2>$null
  $pat = '^## T[0-9]+ .*status: todo( \(meant for (' + [regex]::Escape($Name) + '|any)\))?\s*$'
  $hits = $text | Where-Object { $_ -match $pat }
  if ($hits) { $hits; exit 0 }
  if ((Get-Date) -ge $end) { "no task for $Name yet; run me again"; exit 2 }
  Start-Sleep -Seconds $Interval
}
