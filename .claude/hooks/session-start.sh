#!/bin/bash
# Installs everything the bot needs to run and be tested: ffmpeg (voice and
# video-note transcoding) plus the Python dependencies from the Pipfile.
set -euo pipefail

# Local machines are set up by their owner; only provision the web container.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  SUDO="sudo"
fi

if ! command -v ffmpeg > /dev/null 2>&1 || ! command -v ffprobe > /dev/null 2>&1; then
  echo "Installing ffmpeg..."
  $SUDO apt-get update -qq
  $SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg
fi
ffmpeg -version | head -1

if ! command -v pipenv > /dev/null 2>&1; then
  echo "Installing pipenv..."
  pip3 install --quiet --break-system-packages pipenv
fi

echo "Installing Python dependencies..."
PIPENV_VENV_IN_PROJECT=1 pipenv install --dev

echo 'export PIPENV_VENV_IN_PROJECT=1' >> "${CLAUDE_ENV_FILE:-/dev/null}"
echo "Session setup complete."
