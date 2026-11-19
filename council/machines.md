# Machines and hc

`[machines.<name>]` lists where seats may run; reaching another machine needs `hc`. None listed: this machine.

## Pick the machine (before staffing)

1. Candidates: every listed machine that is not `coordinate_only` and answers `hc exec --on <machine> -- uptime` (this machine: plain `uptime`). No candidate, or no `hc`: this machine, unless it is `coordinate_only`; then report and stop.
2. Load per core = 1-minute load ÷ cores (`nproc` / `sysctl -n hw.ncpu`). On Linux also `free -g`: under 4 GB available drops the machine.
3. Pick the lowest load per core among machines whose `skip` excludes none of the providers you will staff; if none qualifies, the lowest one, and its skipped providers are absent.
4. Every candidate above ~1 per core: tell the user and wait (attended), or retry every 10 minutes for up to an hour and then report (unattended).

All seats of a task run on the picked machine, in one checkout at `<repos>/<owner>/<repo>`; clone it if missing.

## hc

- Launch: `hc run --bg --on <machine> --name <name> --cwd <repo> <interactive line>`; on this machine drop `--on`.
- Collect: `hc wait --children all` returns when every seat is idle or exited; then `hc read --lines 1000 <machine>/<name>` (bare `<name>` locally). For long answers ask the seat to also write them to a file you can `hc file read`.
- Reports: put the literal output of `echo $HC_TERMINAL_ID`, machine-qualified for remote seats (`laptop/t3`), into the brief as `<me>` (empty output: leave the hc send line out and collect by reading), with "also run: hc send <me> \"<seat>: done\"". `codex -s read-only` can't send; collect it by reading.
- A trust dialog is the user's: `hc attach <machine>/<name>`.
- Stop: `hc kill <machine>/<name>`, then `hc rm <machine>/<name>`.
