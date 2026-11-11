#!/bin/sh
# QNX Proof Runner — Gate 1 preflight (machine work, no credentials needed)
# Checks every local prerequisite for building + QEMU-booting the sample.
# Prints PASS / MISSING per item and a summary. Never fakes a pass:
# anything absent is reported MISSING with the fix that resolves it.
# Usage: sh tools/preflight.sh
set -u

pass=0; miss=0
check() {
  label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "PASS    $label"
    pass=$((pass+1))
  else
    echo "MISSING $label — $1_fix"
    miss=$((miss+1))
  fi
}

# Note: the _fix variables below are only used in the MISSING message.
sdp_fix="run the SDP credential-tap sitting (see ~/workspace/your_files/qnx-sdp-credential-tap-sheet-2026-11-09.md)"
qemu_fix="reinstall in the loop: apt-get install -y qemu-system-x86 (.deb 8.2.2 is already in /var/cache/apt/archives; a system install does not survive a runtime restart, so reinstall in the same session as the QEMU boot)"
swc_fix="reinstall QNX Software Center from ~/workspace/qnx-proof-runner/downloads/qnx-setup-2.0.4-202501021438-linux.run"
src_fix="restore src/timing_sample.c from the project repo"
runner_fix="restore tools/proof_runner.py from the project repo"

if [ -d "$HOME/qnx800" ] || [ -f "$HOME/qnx800/qnxsdp-env.sh" ]; then
  echo "PASS    SDP 8.0 baseline at ~/qnx800"; pass=$((pass+1))
else
  echo "MISSING SDP 8.0 baseline at ~/qnx800 — $sdp_fix"; miss=$((miss+1))
fi

if command -v qemu-system-x86_64 >/dev/null 2>&1; then
  echo "PASS    qemu-system-x86_64 ($(qemu-system-x86_64 --version 2>/dev/null | head -1))"; pass=$((pass+1))
else
  echo "MISSING qemu-system-x86_64 — $qemu_fix"; miss=$((miss+1))
fi

if [ -x "$HOME/qnx/qnxsoftwarecenter/qnxsoftwarecenter_clt" ]; then
  echo "PASS    QNX Software Center CLT ($($HOME/qnx/qnxsoftwarecenter/qnxsoftwarecenter_clt -version 2>/dev/null | head -1))"; pass=$((pass+1))
else
  echo "MISSING QNX Software Center CLT — $swc_fix"; miss=$((miss+1))
fi

proj="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$proj/src/timing_sample.c" ]; then
  echo "PASS    sample source src/timing_sample.c"; pass=$((pass+1))
else
  echo "MISSING sample source — $src_fix"; miss=$((miss+1))
fi

if [ -f "$proj/tools/proof_runner.py" ]; then
  echo "PASS    host tool tools/proof_runner.py"; pass=$((pass+1))
else
  echo "MISSING host tool — $runner_fix"; miss=$((miss+1))
fi

if [ -e /dev/kvm ]; then
  echo "INFO    /dev/kvm present (hardware acceleration available)"
else
  echo "INFO    /dev/kvm absent — QEMU will run emulated (slower, still valid for Gate 1)"
fi

echo "---"
echo "Preflight: $pass passed, $miss missing"
[ "$miss" -eq 0 ] && echo "Gate 1 local prerequisites: READY" || echo "Gate 1 local prerequisites: NOT READY (see MISSING lines)"
exit 0
