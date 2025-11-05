# PowerShell helper to untrack common local/sensitive files from git and add .gitignore
# Run from repository root: ./scripts/untrack_sensitive.ps1

$patterns = @(
  ".venv",
  "venv",
  "env",
  "web/node_modules",
  "web/dist",
  ".env",
  ".pytest_cache",
  "__pycache__"
)

Write-Host "This script will attempt to remove these paths from git tracking (if tracked):"
$patterns | ForEach-Object { Write-Host " - $_" }

if (-not (Test-Path .git)) {
  Write-Host "No .git directory found. Initialize a git repo first or run the equivalent git commands manually." -ForegroundColor Yellow
  exit 1
}

foreach ($p in $patterns) {
  if (Test-Path $p) {
    Write-Host "Untracking: $p"
    git rm -r --cached --quiet $p 2>$null
  } else {
    Write-Host "Not present: $p"
  }
}

# Add .gitignore (if exists it will be added)
git add .gitignore

Write-Host "You should commit the changes now with: git commit -m 'chore: ignore local env and build artifacts'"
Write-Host "If you also want to remove the local files/folders from disk, delete them manually or run Remove-Item -Recurse <path> with caution."
