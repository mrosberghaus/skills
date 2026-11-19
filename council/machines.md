# Machines and hc

`[machines.<name>]` in the config lists where seats may run. None listed: this machine.

## Pick the machine

1. For each machine that isn't `coordinate_only`: `uptime`, cores (`nproc` / `sysctl -n hw.ncpu`), and `free -g` on Linux. Lowest load per core wins. All above ~1 per core: say so and queue.
2. All seats of a task go to that one machine (one shared checkout), the implementer's if there is one. Repo at `<repos>/<owner>/<repo>`; clone it if missing.
3. A seat in that machine's `skip` runs on the next machine without it in `skip`, at the same commit; with none left it is absent.

## hc

- Launch: `hc run --bg [--on <machine>] --name <name> --cwd <repo> <launch line>`. Collect: `hc wait --children all`, then `hc read --lines 200 <machine>/<name>`.
- Reports: run `echo $HC_TERMINAL_ID` and write its literal value into the brief as `<me>`, machine-qualified for remote seats (`laptop/t3`); add "also run: hc send <me> \"<seat>: done\"". A `$HC_TERMINAL_ID` written into the brief expands on the seat's side to the seat itself.
- A trust dialog belongs to the user: `hc attach <machine>/<name>`.
- Stop: `hc kill` then `hc rm`.
