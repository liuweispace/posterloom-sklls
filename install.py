#!/usr/bin/env python3
from pathlib import Path
import argparse, os, shutil

REPO=Path(__file__).resolve().parent
SRC=REPO/"posterloom"

def default_target():
    if os.environ.get("POSTERLOOM_SKILLS_DIR"):
        return Path(os.path.expanduser(os.environ["POSTERLOOM_SKILLS_DIR"]))
    if os.environ.get("AGENTS_HOME"):
        return Path(os.path.expanduser(os.environ["AGENTS_HOME"]))/"skills"
    if os.environ.get("CODEX_HOME"):
        return Path(os.path.expanduser(os.environ["CODEX_HOME"]))/"skills"
    agents=Path.home()/".agents"/"skills"
    codex=Path.home()/".codex"/"skills"
    if agents.exists():
        return agents
    if codex.exists():
        return codex
    return agents

def main():
    ap=argparse.ArgumentParser(description="Install PosterLoom into an Agent Skills directory.")
    ap.add_argument("--target", help="Destination skills directory, not the posterloom subfolder.")
    ap.add_argument("--force", action="store_true", help="Replace an existing posterloom installation.")
    args=ap.parse_args()

    if not (SRC/"SKILL.md").exists():
        raise SystemExit("posterloom/SKILL.md not found. Run this installer from the repository.")
    target=Path(os.path.expanduser(args.target)) if args.target else default_target()
    dest=target/"posterloom"
    target.mkdir(parents=True,exist_ok=True)

    if dest.exists():
        if not args.force:
            raise SystemExit(f"{dest} already exists. Re-run with --force to replace it.")
        shutil.rmtree(dest)

    shutil.copytree(SRC,dest)
    print(f"PosterLoom installed to: {dest}")
    print("Reload or restart your host if it does not discover new skills automatically.")

if __name__=="__main__":
    main()
