---
name: council
description: Use before delegating any research, grill, implement or review work on a task, to pick which models do each phase from the project's .council.toml; for "council run" (attended grill, then unattended spec, tickets, implementation, review and opt-in deploy on Matt Pocock's skills); and when the user says "council" or asks several models to weigh one decision. Skip only for plain questions with no task.
argument-hint: "[run <idea|issue> | plan | decide <question> | review <PR>]"
---

# Council

The council staffs tasks: for each phase (research, grill, implement, review) it picks which models do the work, following the config, then runs them. You (whichever agent runs this skill) are the coordinator: you pick, launch, check and synthesize. You are not a seat.

**`council run`**: the full pipeline from grill to deploy. Read [pipeline.md](pipeline.md) and follow it; the sections below still define staffing, seats, the brief and the review gate. After the grill, hand off to an unattended coordinator on the dev machine so the run survives this session: `hc run --bg --on <machine> --outlive-parent --name cr-<slug>-coordinator --cwd Developer/<owner>/<repo> claude --model <[run] coordinator> -- "Use the council skill: council run, resume <spec issue> after go. Report with hc send <me> at each phase change and when done or stuck."` (needs this skill installed on that machine).

## 1. Read the config

Merge, later wins per key:

1. `defaults.toml` beside this file
2. `~/.config/council/council.toml` (user)
3. `<repo>/.council.toml` (project)

Keys per phase: `models` (how many seats; 0 = skip the phase), `prefer` (seat order). A seat is `provider` or `provider:model` (`claude:sonnet`, `codex:gpt-6.2-sol`). The provider counts for `distinct_providers` and `exclude_implementer`; the model only sets strength and cost. Without `:model`, use `[seats.<provider>] model`. Resolve short names through `[seats.<provider>] aliases`; `default` means pass no model flag; anything else passes through as a model ID. Review also: `exclude_implementer`, `max_rounds`, `gate`, `evals`, `final_evals`, `block_on`, `min_score`, `show_score` (see Review gate). `[seats.<provider>] model` pins a model. `[defaults]`: `distinct_providers`, `skip_trivial`. Unknown keys: say so once, ignore them.

## 2. Staff each phase

For each phase, walk `prefer` and take the first `models` seats that are available on the chosen machine (see Seats). With `distinct_providers`, never two seats of one provider in a phase. Review with `exclude_implementer`: skip the implementer's provider when counting; it may add one extra seat, labeled **same-model review**, which never passes a round alone.

If a phase can't be filled, stop and tell the user which seats are missing and why. Never fill it with another model or a duplicate provider silently.

Trivial task (typo, one-liner) with `skip_trivial`: skip research and grill. Review still follows the config.

Show the plan in one table before launching, then proceed without waiting unless something is missing:

```markdown
| Phase | Seats | Machine |
| --- | --- | --- |
| research | Claude Sonnet, Gemini | mini-dev |
| grill | Grok | mini-dev |
| implement | Claude Opus | mini-dev |
| review | Codex, Grok | mini-dev |
```

## 3. Run the phases

- **research**: each seat answers the same research question independently; merge findings, mark where they disagree.
- **grill**: seats attack the plan or spec: wrong assumptions, missing cases, simpler options. You answer what the code can answer; put only the rest to the user, all at once, before implementing.
- **implement**: one seat implements. With `models` > 1, each seat works in its own worktree and branch on the same spec; compare by tests and review, keep one, delete the others.
- **review**: read-only seats return findings (see Review gate). Each round: run `evals`, collect findings, verify each one, fix confirmed ones, re-review with fresh seats. Stop at green or after `max_rounds`; report what remains. Reject feature requests and unrelated refactors as follow-ups.

### Review gate

Each finding from a seat has: severity (`blocker` / `major` / `minor` / `nit`), `file:line`, evidence, suggested fix. You give every finding a verdict against the code: **confirmed**, **rejected** (one-line reason), or **plausible** (can't prove either way; list it, doesn't block). Duplicates across seats merge into one finding.

Green when every entry in `gate` passes:

- `evals`: every command in `evals` exits 0 (run in the implementer's checkout, not by seats). In the round that would turn green, also run `final_evals`.
- `findings`: no confirmed finding open at a `block_on` severity.
- `score`: every counting seat scores ≥ `min_score`.

With `show_score`, seats also give N/10; it is reported but gates only when `score` is in `gate`. Same-model review findings count once confirmed (verification is yours), but its score never counts.

Research, grill and review seats are read-only. Only implement seats edit, and only their own worktree.

## Seats

| Provider | Launch (`<task>` = the brief) | Notes |
| --- | --- | --- |
| claude | `claude --model <model> --disallowedTools Edit Write NotebookEdit Agent -- "<task>"` | Always pass `--model`. Implement seats drop `--disallowedTools`. Not `--permission-mode plan`: it stops at a plan-approval prompt. |
| codex | `codex --no-daemon -s read-only [-m <model>] "<task>"` | Implement: `-s workspace-write`. Read-only blocks `hc send`: collect with `hc read`. |
| grok | `grok [-m <model>] "<task>"` | Read-only by instruction only. First launch in a folder: trust dialog, ask the user to accept (`hc attach <machine>/<name>`). |
| gemini | `agy --mode auto --sandbox --model <model> -i "<task>"` | Models via `[seats.gemini] aliases` (default `neon` = `gemini-4-neon-high`; `neon-xhigh`, `hydrogen`, `carbon`, `argon`, `flash`); never its Claude/GPT models. Works on homer and mini-dev. On cyclone-dev auto mode is missing, so every command asks permission: run this seat on mini-dev instead. |

A seat is unavailable when its CLI is missing, not signed in, or fails to start: report **absent: <reason>**.

## Where seats run

1. Dev machines via `hc run --bg --on <machine>`. Before launching, check `uptime`, cores (`nproc` / `sysctl -n hw.ncpu`) and `free -g` on cyclone-dev; lower load per core wins. Both above ~1 per core: say so and queue.
2. All seats of a task on one machine (shared checkout); the implementer's machine if one exists. Repo at `~/Developer/<owner>/<repo>`; clone if missing.
3. Locally only when there is no repo or both machines are unreachable.

```sh
echo $HC_TERMINAL_ID   # write the literal value, e.g. homer/t9t, into <me>
hc run --bg --on mini-dev --name council-review-codex --cwd Developer/<owner>/<repo> codex --no-daemon -s read-only "<task>"
hc wait --children all
hc read --lines 200 mini-dev/council-review-codex
```

## The brief

Every seat in a phase gets the same brief and nothing else: not this conversation, not another seat's answer.

```text
You are one <phase> seat on a model council. <Read-only: do not edit files, commit, or start agents. | Implement in this worktree only; do not start agents.>

Task: <one sentence>
Where to look: <repo, branch/PR, files, symbols>
Context: <constraints, success criteria, known concerns; compact>

Answer with: position or result; evidence (files/lines checked); biggest risk; what others may miss.<review: instead, a list of findings, each: severity (blocker/major/minor/nit), file:line, evidence, suggested fix. <show_score: then Score N/10.>>

End your final message with the full answer. If you can, also run: hc send <me> "<seat>: done"
```

If `jg` (Jevgrep) is installed, use it to find **Where to look**; otherwise `rg` and reads.

## Decide mode

`council decide <question>`: one round, all available providers (or the user's named seats), read-only, brief as above. Write your own position first. Output one row per seat (position, key reason), then **Consensus**, **Strongest dissent** (always shown), **Premise check**, **Recommendation** with its evidence.

## Report

- On a PR, add to the description (edit it, don't comment), before the model/harness line:

  ```markdown
  ## Council

  Seats: implement Claude Opus · review Codex, Grok (mini-dev)

  | Round | Evals | Blocker | Major | Minor | Nit | Rejected | Scores |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | 1 | 1/2 failing | 1 | 2 | 3 | 1 | 2 | Codex 7, Grok 6 |
  | 2 | green | 0 | 0 | 1 | 1 | 0 | Codex 9, Grok 9 |
  ```

  Counts are confirmed findings. Drop the Scores column without `show_score`; `absent` / `no score` where it applies; never invent a score.
- `hc kill` and `hc rm` every council terminal you started.
- Say which machine and model each seat used and which were absent.
