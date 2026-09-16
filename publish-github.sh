#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${1:-posterloom}"
VISIBILITY="${2:-public}"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required: https://cli.github.com/"
  exit 1
fi

gh auth status >/dev/null

cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -d .git ]; then
  git init
  git add .
  git commit -m "Release PosterLoom v1.0.0"
  git branch -M main
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "An origin remote already exists:"
  git remote get-url origin
  echo "Push manually or remove the existing remote before using this publisher."
  exit 1
fi

case "$VISIBILITY" in
  public|private) ;;
  *) echo "Visibility must be public or private."; exit 1 ;;
esac

gh repo create "$REPO_NAME" "--$VISIBILITY" --source=. --remote=origin --push
echo "PosterLoom published: $REPO_NAME"
