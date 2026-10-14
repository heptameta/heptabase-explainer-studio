#!/bin/sh
# Install or update the explainer-studio command for this user to the latest release, then install what videos need
# (explainer-studio setup). Safe to run again. Never asks for an administrator password.
#
#   sh install.sh                      (from the skill folder)
#   curl -fsSL <url>/install.sh | sh
#
# EXPLAINER_STUDIO_SOURCE overrides where the package comes from, for example a local checkout during development.
# UV_NO_MODIFY_PATH=1 leaves shell profiles alone.
set -eu

REPO="heptameta/heptabase-explainer-studio"  # written by scripts/release.py
SOURCE="${EXPLAINER_STUDIO_SOURCE:-}"  # empty: the latest release; a dev build's snapshot writes its folder here

step() { printf '\n== %s\n' "$1"; }
fail() { printf 'error: %s\n' "$1" >&2; exit 1; }

case "$(uname -s)" in
  MINGW* | MSYS* | CYGWIN*)
    here="$(dirname "$0")"
    if [ -f "$here/install.ps1" ] && command -v powershell.exe >/dev/null 2>&1; then
      exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$here/install.ps1")"
    fi
    fail "on Windows, run in PowerShell: powershell -ExecutionPolicy Bypass -File install.ps1 (or: irm <url>/install.ps1 | iex)"
    ;;
esac

step "uv (Python tool manager)"
UV="$(command -v uv 2>/dev/null || true)"
if [ -z "$UV" ]; then
  for candidate in "${XDG_BIN_HOME:-$HOME/.local/bin}/uv" "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
    if [ -x "$candidate" ]; then UV="$candidate"; break; fi
  done
fi
if [ -z "$UV" ]; then
  echo "installing uv into your home folder (astral.sh/uv)"
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    fail "curl or wget is needed to install uv"
  fi
  for candidate in "${XDG_BIN_HOME:-$HOME/.local/bin}/uv" "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
    if [ -x "$candidate" ]; then UV="$candidate"; break; fi
  done
  [ -n "$UV" ] || fail "uv was installed but cannot be found; open a new terminal and run this script again"
fi
echo "uv: $UV ($("$UV" --version))"

step "git"
# ManimGL (and the default package source) are fetched with git
if [ "$(uname -s)" = "Darwin" ] && ! xcode-select -p >/dev/null 2>&1; then
  fail "git is missing: run \`xcode-select --install\` (Apple's command line tools), then run this script again"
fi
git --version >/dev/null 2>&1 || fail "git is missing: install it with your package manager, then run this script again"
echo "git: $(git --version)"

if [ -z "$SOURCE" ]; then
  step "the latest release"
  # the highest v<major>.<minor>.<patch> tag
  LATEST="$(GIT_TERMINAL_PROMPT=0 git ls-remote --tags --refs "https://github.com/$REPO.git" 'v*' 2>/dev/null \
    | sed -n 's|.*refs/tags/v\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)$|\1|p' \
    | sort -t. -k1,1n -k2,2n -k3,3n | tail -n 1)"
  [ -n "$LATEST" ] || fail "cannot read the releases of github.com/$REPO: check the network and run this again"
  echo "explainer-studio $LATEST"
  SOURCE="git+https://github.com/$REPO@v$LATEST"
fi

step "explainer-studio"
if [ -d "$SOURCE" ]; then
  # a local checkout: rebuild it every time, since its version number does not change between edits
  SPEC="explainer-studio @ file://$(cd "$SOURCE" && pwd)"
  "$UV" tool install --python 3.13 --force --reinstall-package explainer-studio "$SPEC"
else
  "$UV" tool install --python 3.13 --force "explainer-studio @ $SOURCE"
fi
BIN="$("$UV" tool dir --bin)"
STUDIO="$BIN/explainer-studio"
[ -x "$STUDIO" ] || fail "the install finished but $STUDIO is missing"
case ":$PATH:" in
  *":$BIN:"*) ;;
  *)
    if [ -z "${UV_NO_MODIFY_PATH:-}" ]; then
      "$UV" tool update-shell >/dev/null 2>&1 || true
      echo "added $BIN to PATH in your shell profile; new terminals find explainer-studio"
    fi
    echo "until then, run it as $STUDIO"
    ;;
esac

step "explainer-studio setup (ffmpeg, LaTeX, fonts, map data, a test render)"
if ! "$STUDIO" setup; then
  echo
  echo "setup did not finish: fix the problems above, then run: $STUDIO setup" >&2
  exit 1
fi
echo
echo "installed: $("$STUDIO" --version) at $STUDIO"
