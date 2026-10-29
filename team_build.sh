#!/usr/bin/env bash
# One-shot setup for a fresh Ubuntu (WSL or native). Run from the repo root:
#   bash team_build.sh
#
# Installs: Java 21, Python 3.12 (via uv, in .venv), the libraries the client needs,
# then builds the project, downloads the engine + client, and plays a test match.
set -euo pipefail
cd "$(dirname "$0")"

step() { echo; echo "==> $*"; }

# Running from the Windows drive (/mnt/c/...) is very slow and breaks file permissions
if [[ "$PWD" == /mnt/* ]]; then
  echo "WARNING: this repo is on the Windows filesystem ($PWD)."
  echo "Clone it inside WSL instead (e.g. ~/battle-bot) for much faster builds."
  read -rp "Continue anyway? [y/N] " answer
  [[ "$answer" == [yY]* ]] || exit 1
fi

# Fix Windows line endings if the repo was cloned/edited on the Windows side
if grep -q $'\r' gradlew 2>/dev/null; then
  step "Converting Windows line endings (CRLF -> LF) in scripts"
  sed -i 's/\r$//' gradlew ./*.sh
fi
chmod +x gradlew run_client.sh

step "Installing system packages (needs sudo)"
sudo apt-get update
sudo apt-get install -y \
  openjdk-21-jdk curl unzip git ca-certificates \
  libwebkit2gtk-4.1-0 libegl1 libgl1-mesa-dri \
  libwayland-client0 libwayland-egl1 libwayland-cursor0 fonts-dejavu-core

# gradle.properties pins org.gradle.java.home to this path
JAVA21=/usr/lib/jvm/java-21-openjdk-amd64
if [ ! -x "$JAVA21/bin/java" ]; then
  echo "Java 21 not found at $JAVA21. Install it, or edit org.gradle.java.home in gradle.properties." >&2
  exit 1
fi

step "Installing uv (Python manager)"
if ! command -v uv > /dev/null && [ ! -x "$HOME/.local/bin/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

step "Creating Python 3.12 virtualenv in .venv"
if [ ! -x .venv/bin/python ] || ! .venv/bin/python -c 'import sys; sys.exit(sys.version_info[:2] != (3, 12))'; then
  rm -rf .venv
  uv venv --python 3.12 --seed .venv
fi

step "Building project and downloading engine + client"
./gradlew build

step "Installing Python engine package"
./gradlew downloadPyPackage

step "Playing a test match"
./gradlew run

echo
echo "Setup complete!"
echo "  Run a match:        ./gradlew run          (teams/map set in gradle.properties)"
echo "  Watch replays:      ./run_client.sh        (replays are saved in matches/)"
echo "  Make a submission:  .venv/bin/python run.py zip_submission"
