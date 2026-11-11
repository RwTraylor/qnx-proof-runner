#!/usr/bin/env python3
"""QNX Proof Runner — host tool (Developer Tooling & Host Tools).

Builds the bundled QNX sample application with the QNX SDP 8.0
toolchain, boots it under QEMU, captures its timing output, verifies
the result against an acceptance envelope, and writes a hash-chained
verification report (report.json + report.md).

Honesty contract: if the SDP is not installed, or the build fails, or
QEMU produces no SAMPLE_RESULT line, the tool says exactly that and
exits non-zero. It never fabricates a pass.

Usage:
    python3 proof_runner.py [--sdp ~/qnx800] [--period-ms 10]
                            [--iterations 200] [--out runs/latest]

The SDP path resolution order: --sdp, $QNX_HOST/$QNX_TARGET from a
sourced qnxsdp-env, ~/qnx800.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

TOOL_VERSION = "0.1.0-spike"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Chain:
    """A tiny hash chain for report entries: each entry names the
    hash of the previous one, so the report's history can't be
    quietly reordered or edited."""

    def __init__(self) -> None:
        self.entries: list[dict] = []
        self.prev = "GENESIS"

    def add(self, kind: str, detail: dict) -> dict:
        entry = {
            "seq": len(self.entries),
            "kind": kind,
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "prev": self.prev,
            "detail": detail,
        }
        blob = json.dumps(entry, sort_keys=True).encode()
        entry["hash"] = sha256_hex(blob)
        self.prev = entry["hash"]
        self.entries.append(entry)
        return entry


def find_sdp(explicit: str | None) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    if os.environ.get("QNX_HOST"):
        candidates.append(Path(os.environ["QNX_HOST"]).parent)
    candidates.append(Path.home() / "qnx800")
    for cand in candidates:
        if (cand / "host").exists() or list(cand.glob("qnxsdp-env*")):
            return cand
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="QNX Proof Runner")
    ap.add_argument("--sdp", default=None, help="path to the SDP install")
    ap.add_argument("--period-ms", type=int, default=10)
    ap.add_argument("--iterations", type=int, default=200)
    ap.add_argument("--out", default="runs/latest")
    args = ap.parse_args(argv)

    chain = Chain()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    chain.add("run_started", {"tool": TOOL_VERSION,
                              "period_ms": args.period_ms,
                              "iterations": args.iterations})

    sdp = find_sdp(args.sdp)
    if sdp is None:
        chain.add("blocked", {"reason": "QNX SDP 8.0 not found",
                              "looked_for": ["--sdp", "$QNX_HOST", "~/qnx800"]})
        _write_report(chain, out_dir, passed=False)
        print("BLOCKED: QNX SDP 8.0 not installed in this loop yet.")
        print(f"Report: {out_dir / 'report.json'}")
        return 3

    chain.add("sdp_found", {"sdp": str(sdp)})
    # Spike path: build + QEMU boot + capture + verify get wired here
    # once the toolchain is installed in the loop (Phase 0 continues).
    chain.add("blocked", {"reason": "build/qemu stage not wired yet (spike)"})
    _write_report(chain, out_dir, passed=False)
    print("SDP found; build/QEMU stage is the next spike step.")
    return 3


def _write_report(chain: Chain, out_dir: Path, *, passed: bool) -> None:
    payload = {"passed": passed, "entries": chain.entries}
    (out_dir / "report.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# QNX Proof Runner — report", "",
             f"Result: {'PASS' if passed else 'NOT PASSED'}", ""]
    for e in chain.entries:
        lines.append(f"- [{e['seq']}] {e['kind']} — {e['detail']} "
                     f"(hash {e['hash'][:12]}…)")
    (out_dir / "report.md").write_text("\n".join(lines) + "\n",
                                       encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
