# Machines and hc

`[machines.<name>]` lists where seats may run; reaching another machine needs `hc`. None listed: this machine.

## Pick the machine (with staffing)

1. Candidates: every listed machine that is not `coordinate_only` and answers `hc exec --on <machine> -- uptime` (this machine: plain `uptime`). No candidate, or no `hc`: this machine, unless it is `coordinate_only`; then report and stop.
2. Load per core = 1-minute load ÷ cores (`nproc` / `sysctl -n hw.ncpu`). On Linux also `free -g`: under 4 GB available drops the machine.
3. Every candidate above ~1 per core: tell the user and wait (attended), or retry every 10 minutes for up to an hour, then report and stop (unattended).
4. Staff every phase in scope (SKILL.md section 2) as if on each remaining candidate. Prefer the candidates where every phase with `models > 0` gets at least one seat, then the fewest shortfalls; break ties by load per core.

All seats of a task run on the picked machine: in the current checkout locally, or at `<repos>/<owner>/<repo>` remotely (clone it if missing); implement and merge seats use worktrees of it.

Done when one machine is picked and its checkout is current, or you stopped and reported.

## hc

- Launch: `hc run --bg --on <machine> --name <name> --cwd <repo> <interactive line>`; on this machine drop `--on`.
- Collect: `hc wait --children all` returns when every seat is idle or exited; then `hc read --lines 1000 <machine>/<name>` (bare `<name>` locally). Truncated: read again with a larger `--lines`.
- Reports: put the literal output of `echo $HC_TERMINAL_ID`, machine-qualified for remote seats (`laptop/t3`), into the brief as `<me>` (empty output: leave the hc send line out and collect by reading), with "also run: hc send <me> \"<seat>: done\"". Sandboxed seats (`codex -s read-only`, `agy --sandbox`) may fail to send: always collect by reading too.
- A trust dialog is the user's: `hc attach <machine>/<name>`.
- Stop: `hc kill <machine>/<name>`, then `hc rm <machine>/<name>`.
