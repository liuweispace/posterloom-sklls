param(
  [string]$RepoName = "posterloom",
  [ValidateSet("public","private")]
  [string]$Visibility = "public"
)

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Error "GitHub CLI (gh) is required: https://cli.github.com/"
  exit 1
}

gh auth status
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not (Test-Path ".git")) {
  git init
  git add .
  git commit -m "Release PosterLoom v1.0.0"
  git branch -M main
}

git remote get-url origin *> $null
if ($LASTEXITCODE -eq 0) {
  Write-Error "An origin remote already exists. Push manually or remove it before using this publisher."
  exit 1
}

gh repo create $RepoName "--$Visibility" --source=. --remote=origin --push
