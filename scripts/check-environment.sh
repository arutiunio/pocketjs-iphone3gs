#!/usr/bin/env bash
set -u

echo "== Host tools =="
for cmd in bun rustup xcrun ldid idevice_id ideviceinfo iproxy ssh scp zip unzip hdiutil; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf "[ok] %-12s %s\n" "$cmd" "$(command -v "$cmd")"
  else
    printf "[missing] %s\n" "$cmd"
  fi
done

echo
echo "== Rust =="
rustup toolchain list 2>/dev/null || true
rustup component list --toolchain nightly-2026-07-02 2>/dev/null | grep 'rust-src' || true

echo
echo "== USB devices =="
idevice_id -l 2>/dev/null || true

echo
echo "== Xcode 26.6 =="
if [ -d /Applications/Xcode-26.6.app ]; then
  DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer xcodebuild -version 2>/dev/null || true
  DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer xcrun --find ld-classic 2>/dev/null || true
else
  echo "[missing] /Applications/Xcode-26.6.app"
fi

echo
echo "== PocketJS cache =="
for p in   "$HOME/.cache/pocket-stack/iphone4s/sysroot-6.1.3"   "$HOME/.cache/pocket-stack/ipodtouch4/ssh/id_rsa"   "$HOME/.cache/pocket-stack/ipodtouch4/ssh/known_hosts"; do
  if [ -e "$p" ]; then
    echo "[ok] $p"
  else
    echo "[missing] $p"
  fi
done
