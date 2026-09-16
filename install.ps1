param(
  [string]$Target = "",
  [switch]$Force
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$argsList = @()
if ($Target) { $argsList += "--target"; $argsList += $Target }
if ($Force) { $argsList += "--force" }
python "$ScriptDir\install.py" @argsList
