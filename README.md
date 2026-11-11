# QNX Proof Runner

A developer tool for QNX 8.0: it builds a small QNX application,
boots it under QEMU, captures the application's real-time timing
output, verifies it against an acceptance envelope, and issues a
signed, hash-chained verification report — proof, not promises, for
"it ran on QNX."

**QNX Global Hackathon 2026 — Category: Developer Tooling & Host Tools**
(plus a codelab for the Best Codelab / Tutorial bonus; see `CODELAB.md`
when it lands in Phase 2.)

## Status

Phase 0 (spike): project scaffolded; host tool skeleton in place.
Progress 2026-11-09: all eight SDP 8.0 licenses are accepted and
deployed in myQNX, and QNX Software Center 2.0.4 is now installed in
this build loop at `~/qnx/qnxsoftwarecenter` (headless install from
the byte-verified installer; its command-line tool
`qnxsoftwarecenter_clt` runs and reports version 2.0.4). Still
blocked, honestly: the SDP 8.0 baseline itself is not yet installed —
fetching it requires a myQNX credential sync
(`qnxsoftwarecenter_clt -syncLicenseKeys` / `-installBaseline`),
which is Ricket's login gate.
Progress 2026-11-10 (Gate 1 spike pulled forward): QEMU reinstalled
in the loop (QEMU emulator version 8.2.2, verified) and the Software
Center's connection test PASSES — network egress to qnx.com works.
The sync was attempted without credentials and the server answered
verbatim: "Credentials for myQNX are required for license key sync,
use -myqnx.user, -myqnx.password option to set them", and a metadata
mirror attempt answered "Request requires authorization". Local
license directories (~/.qnx/license, /root/.qnx/license) are empty —
nothing syncs from local state. So the ONLY remaining blocker for
Gate 1 is that one credential sync (Ricket's tap); no credential was
attempted by the machine. Preflight now reads 4 passed / 1 missing
(SDP only). Proof-runner report from this state:
`runs/gate1-2026-11-10/report.json` in the local working copy (a
local run artifact, not tracked in this repository; honest BLOCKED,
exit 3). The
sample application's source is complete.

## Layout

- `src/timing_sample.c` — the QNX-native sample: a periodic task that
  measures its own wakeup lateness with the QNX cycle counter
  (`ClockCycles`, system-page `cycles_per_sec`) and prints a
  `SAMPLE_RESULT` line.
- `tools/proof_runner.py` — the host tool (Python 3, stdlib only):
  build → QEMU boot → capture → verify → hash-chained report.

## Build and run

Requirements: QNX SDP 8.0 (free for non-commercial use via
QNX Everywhere), QEMU (x86_64 target), Python 3.

```sh
# 1. Build the sample with the SDP toolchain
source ~/qnx800/qnxsdp-env.sh
qcc -V gcc_ntox86_64 -Wall -O2 -o timing_sample src/timing_sample.c

# 2. Run the proof (builds, boots QEMU, verifies, writes a report)
python3 tools/proof_runner.py --out runs/latest
```

Exact target image and QEMU invocation are pinned in Phase 0 once the
toolchain is installed and the quick-start image is in hand; this
README is updated with the verified commands at that point — nothing
here is claimed before it has run.

## License

MIT — see `LICENSE`.
