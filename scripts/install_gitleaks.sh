#!/bin/sh
# Install the pinned gitleaks release into <dir> after a SHA-256 check.
# Usage: scripts/install_gitleaks.sh <dir>   (Linux x64 only, as on the CI runners)
set -eu
VERSION=8.30.1
SHA256=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
dir=$1
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/gitleaks.tar.gz" \
  "https://github.com/gitleaks/gitleaks/releases/download/v$VERSION/gitleaks_${VERSION}_linux_x64.tar.gz"
echo "$SHA256  $tmp/gitleaks.tar.gz" | sha256sum -c -
mkdir -p "$dir"
tar -xzf "$tmp/gitleaks.tar.gz" -C "$dir" gitleaks
"$dir/gitleaks" version
