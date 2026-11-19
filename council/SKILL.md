---
name: council
description: Multi-model council. Use before delegating research, grill, implement or review work; for `council review <PR>`; for `council run` (grill to deploy, experimental); for `council decide` on a tradeoff.
argument-hint: "[review <PR> | run <idea|issue> | decide <question>]"
---

# Council

You are the **coordinator**: you staff each phase in scope with **seats** (one model each, ideally from distinct providers), brief them, verify what they return, and report.

Branches:

- `council run`: follow [pipeline.md](pipeline.md); it uses every section below.
- `council decide`: [Decide](#decide), which uses sections 1, 3 and 4.
- `council review <PR>` and delegated work: sections 1–6.
- `[machines]` configured or `hc` installed: read [machines.md](machines.md) before staffing (section 2 or Decide).

## 1. Config

Merge [defaults.toml](defaults.toml) (every key, with its type and values), `~/.config/council/council.toml`, then `<repo>/.council.toml`; later wins per key within each section.

**Trust boundary.** For `council review <PR>` and `council run`, the repo layer is `git show origin/<default>:.council.toml` (after `git fetch origin`; `<default>` from `git symbolic-ref refs/remotes/origin/HEAD`), never the branch under review or a branch the run produced. `[ship]` comes from that file or `defaults.toml`, never from user config. Without an `origin` remote: the local default branch's file, with `merge` capped at `ready`.

A seat is `provider` or `provider:model`. Resolve the model: the seat's `:model`, else `[seats.<provider>] model`; then through `[seats.<provider>] aliases`. `default` means the CLI's configured model (omit the flag where the launch line marks it optional).

Done when every key in scope has one value and you know where `[ship]` came from.

## 2. Staff

The phases in scope: the ones the task needs (with `skip_trivial`, a typo-sized task drops research and grill). For each, walk `prefer` and take the first `models` seats that can run here. A seat that can't (CLI missing, not signed in, fails to start, in the machine's `skip`) is **absent: <reason>**.

- `distinct_providers = true`: one seat per provider. When fewer providers are available than `models`, staff the ones there are and mark the phase **short: k of n**.
- `distinct_providers = false`: a provider may fill several seats with different models.
- Review with `exclude_implementer = true`: the **implementer** is the provider that wrote the change (run state, `Co-Authored-By` trailers, the PR's model line, or the user). Skip it in `prefer` while any other provider is available. When none is, staff it anyway: the review is **not independent**; it can turn green on `evals` and `findings`, its scores never count, and it caps `[ship] merge` at `ready`.
- A phase with `models > 0` and zero seats stops the task: report what is missing.

Done when every phase in scope has its seats or a recorded shortfall. Show one table (phase, seats with models, machine, shortfalls) and proceed.

## 3. Brief

Send every seat in a phase the identical brief, independently; seats see neither this conversation nor each other's answers.

```text
You are one <phase> seat on a model council. <Read-only: change no files, start no agents. | Implement in this worktree only; start no agents.>
Task: <one sentence>
Where to look: <repo, branch/PR, files; for a branch you don't have checked out: git diff / git show <branch>:<file>>
Context: <constraints, success criteria, known concerns>
Answer: position or result; evidence (file:line); biggest risk; what others may miss.
<review: findings instead, each with severity (blocker/major/minor/nit), file:line, evidence, fix, or "No findings"; then Score N/10 when show_score or "score" in gate.>
End your final message with the full answer.
```

Write the brief to a file outside the repo and pass it as `"$(cat <file>)"`, so quoting can't break it. Done when every seat's brief file exists.

## 4. Launch and collect

| Provider | Interactive (hc) | Print mode (no hc) | Notes |
| --- | --- | --- | --- |
| claude | `claude --model <model> --permission-mode auto [--disallowedTools Edit Write NotebookEdit Agent] -- "<brief>"` | `claude -p --model <model> --permission-mode auto [--disallowedTools Edit Write NotebookEdit Agent] -- "<brief>" > <out>` | Always `--model`. Read-only seats keep `--disallowedTools`. Plan mode stalls on an approval prompt. |
| codex | `codex --no-daemon -a never -s read-only [-m <model>] "<brief>"` | `codex --no-daemon exec -s read-only [-m <model>] -o <out> "<brief>" > <log> 2>&1` | `--no-daemon` goes before `exec`. Implement: `-s workspace-write`. |
| grok | `grok --permission-mode auto [-m <model>] "<brief>"` | `grok -p "<brief>" --permission-mode auto [-m <model>] > <out>` | Read-only by the brief. Trust dialog on each new folder: run it in an already trusted checkout. |
| gemini | `agy --mode auto --sandbox --model <model> -i "<brief>"` | `agy -p --mode auto --sandbox --model <model> "<brief>" > <out>` | Only its Gemini models; read-only by the brief; the sandbox blocks network. Where `agy` offers no auto mode (the status bar shows none), every command prompts: put `gemini` in that machine's `skip`. |

Without `hc`: start each print-mode line in the background and read `<out>` whole once it exits. With or without `hc`, a seat that crashes, gives an empty answer, or runs past `[defaults] seat_timeout` minutes is stopped and absent; take the next seat in `prefer`. A harness that runs a seat's own provider may run that seat as its subagent instead, with the seat's model and a fresh context.

Done when every seat has returned an answer or is absent.

## 5. Verify

- **research**: merge findings, mark disagreements.
- **grill**: answer what the code answers; ask the user the rest in one round.
- **implement** with `models` > 1: one worktree per seat; keep the attempt that wins on tests and review, delete the others.
- **review**: give every finding a verdict against the code: **confirmed**, **rejected** (one-line reason) or **plausible** (reported, non-blocking). Merge duplicates. Who fixes confirmed findings: the run's implementer seat, or for `council review <PR>` a fresh `[implement]` seat when the user asked for fixes, otherwise nobody (report only). Re-review with fresh seats after fixes. Feature requests and unrelated refactors go to the report's **Follow-ups**.

A review is **green** when every entry of `gate` passes:

- `evals`: every command exits 0; in a PR or final review's round that would turn green, `final_evals` too (a failure there starts another round). Run them in a checkout of the branch under review. When every eval list in scope is empty, the gate reads **evals: none configured** in every report and passes.
- `findings`: no confirmed finding with a severity in `block_on` is open.
- `score`: at least one counting seat, and every counting seat gives ≥ `min_score`; a counting seat without a score is absent for scoring.

Done: research and grill when the merged answer is written; implement when the kept attempt is committed; review at green, after round 1 when it is report-only, or at `max_rounds` with what remains open listed.

## 6. Report

- On a PR: put a `## Council` section in the description (replace an existing one; else insert it before a model/harness footer; else append): seats per phase, shortfalls, one row per round (evals, confirmed findings per severity, plausible, rejected, scores when `show_score`). Every number comes from a seat; write `absent` or `no score` where true.
- Elsewhere: the same section in your final message.
- **Follow-ups**: the out-of-scope findings.
- Stop every seat you started.

Done when the section is written and no seat of yours is still running.

## Decide

`council decide <question>`:

1. Seats: one per available provider, at its `[seats.<provider>] model` (or the seats the user names).
2. Write your own position and its reasons, as the coordinator's baseline.
3. Brief and launch (sections 3–4), read-only; collect.
4. Output one row per seat, then **Consensus**, **Strongest dissent** (always shown), **Premise check**, **Recommendation** with its evidence.
5. Stop every seat.

Done when the recommendation names the evidence that decided it and no seat is running.
