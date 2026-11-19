---
name: council
description: Multi-model council. Use before delegating research, grill, implement or review work; for `council review <PR>`; for `council run` (grill to deploy); for `council decide` on a tradeoff.
argument-hint: "[review <PR> | run <idea|issue> | decide <question>]"
---

# Council

You are the **coordinator**: you staff each phase in scope with **seats** (one model each, ideally from distinct providers), brief them, verify what they return, and report.

Branches:

- `council run`: follow [pipeline.md](pipeline.md); it uses every section below.
- `council decide`: sections 1–4, then [Decide](#decide).
- `council review <PR>` and delegated work: sections 1–6.
- `[machines]` configured or `hc` installed: read [machines.md](machines.md) before section 2.

## 1. Config

Merge [defaults.toml](defaults.toml) (every key, with its type and values), `~/.config/council/council.toml`, then `<repo>/.council.toml`; later wins per key within each section.

**Trust boundary.** Run `git fetch origin`, then take `[ship]` and the `[review]` keys `gate`, `evals`, `final_evals`, `block_on` only from `git show origin/<default>:.council.toml`; where that file lacks them, from `defaults.toml`. A branch under review or produced by a run sets everything else.

A seat is `provider` or `provider:model`. The provider sets diversity, the model sets strength. Resolve the model: the seat's `:model`, else `[seats.<provider>] model`; then through `[seats.<provider>] aliases`. `default` means the CLI's configured model (omit the flag where the launch line marks it optional).

Done when every key in scope has one value and you know where `[ship]` came from.

## 2. Staff

The phases in scope: the ones the task needs (with `skip_trivial`, a typo-sized task drops research and grill). For each, walk `prefer` and take the first `models` seats that can run here. A seat that can't (CLI missing, not signed in, fails to start, in the machine's `skip`) is **absent: <reason>**.

- `distinct_providers = true`: one seat per provider. When fewer providers are available than `models`, staff the ones there are and mark the phase **short: k of n**.
- `distinct_providers = false`: a provider may fill several seats with different models.
- Review with `exclude_implementer = true`: the **implementer** is the provider that wrote the change (run state, `Co-Authored-By` trailers, the PR's model line, or the user). Its seats are **implementer seats**: their confirmed findings count, their scores do not, and they can't make a review green alone. When only the implementer's provider is available, the review still runs on implementer seats and is reported **not independent**.
- A phase with zero seats stops the task: report what is missing.

Done when every phase in scope has its seats or a recorded shortfall. Show one table (phase, seats with models, machine, shortfalls) and proceed.

## 3. Brief

Send every seat in a phase the identical brief, independently; seats see neither this conversation nor each other's answers.

```text
You are one <phase> seat on a model council. <Read-only: change no files, start no agents. | Implement in this worktree only; start no agents.>
Task: <one sentence>
Where to look: <repo, branch/PR, files; for a branch you don't have checked out: git diff / git show <branch>:<file>>
Context: <constraints, success criteria, known concerns>
Answer: position or result; evidence (file:line); biggest risk; what others may miss.
<review: findings instead, each with severity (blocker/major/minor/nit), file:line, evidence, fix, or "No findings"; <show_score: then Score N/10.>>
End your final message with the full answer.
```

Write the brief to a file and pass it as `"$(cat <file>)"`, so quoting can't break it.

## 4. Launch and collect

| Provider | Interactive (hc) | Print mode (no hc) | Notes |
| --- | --- | --- | --- |
| claude | `claude --model <model> --permission-mode auto [--disallowedTools Edit Write NotebookEdit Agent] -- "<brief>"` | `claude -p --model <model> --permission-mode auto … "<brief>"` | Always `--model`. Read-only seats keep `--disallowedTools`. Plan mode stalls on an approval prompt. |
| codex | `codex --no-daemon -a never -s read-only [-m <model>] "<brief>"` | `codex --no-daemon exec -s read-only [-m <model>] -o <out> "<brief>"` | `--no-daemon` goes before `exec`. Implement: `-s workspace-write`. Read-only can't `hc send`: read its screen or `<out>`. |
| grok | `grok --permission-mode auto [-m <model>] "<brief>"` | `grok -p "<brief>" --permission-mode auto [-m <model>]` | Read-only only by the brief. Trust dialog on each new folder: use it read-only in an already trusted checkout. |
| gemini | `agy --mode auto --sandbox --model <model> -i "<brief>"` | `agy -p --mode auto --sandbox --model <model> "<brief>"` | Only its Gemini models. Where `agy` offers no auto mode (the status bar shows none), every command prompts: put `gemini` in that machine's `skip`. |

Without `hc`: start each print-mode line as a background process with output to `<out>`, wait for it to exit, read `<out>` whole. A non-zero exit, a timeout or an empty answer makes the seat absent. A harness with its own subagents may run Claude seats as subagents instead.

Done when every seat has returned an answer or is absent.

## 5. Verify

- **research**: merge findings, mark disagreements.
- **grill**: answer what the code answers; ask the user the rest in one round.
- **implement** with `models` > 1: one worktree per seat; keep the attempt that wins on tests and review, delete the others.
- **review**: give every finding a verdict against the code: **confirmed**, **rejected** (one-line reason) or **plausible** (reported, non-blocking). Merge duplicates. Who fixes confirmed findings: the run's implementer seat, or for `council review <PR>` a fresh `[implement]` seat when the user asked for fixes, otherwise nobody (report only). Re-review with fresh seats after fixes. Feature requests and unrelated refactors go to the report's **Follow-ups**.

A review is **green** when every entry of `gate` passes:

- `evals`: every command exits 0; in the round that would turn green, `final_evals` too (a failure there starts another round). Empty `evals`: the gate reads **evals: none configured** in every report and passes.
- `findings`: only nits, minors or plausible findings remain open below `block_on`.
- `score`: every counting seat gives ≥ `min_score`; a counting seat without a score is asked once more, then absent.

Done at green, or at `max_rounds` with what remains open listed.

## 6. Report

- On a PR: put a `## Council` section in the description (replace an existing one; else insert it before a model/harness footer; else append): seats per phase, shortfalls, one row per round (evals, confirmed findings per severity, plausible, rejected, scores when `show_score`). Every number comes from a seat; write `absent` or `no score` where true.
- Elsewhere: the same section in your final message.
- **Follow-ups**: the out-of-scope findings.
- Stop every seat you started.

Done when the section is written and no seat of yours is still running.

## Decide

`council decide <question>`: one read-only round, every available provider (or the seats the user names). Your own position goes first, as the coordinator's baseline, before you read the seats. Then one row per seat, **Consensus**, **Strongest dissent** (always shown), **Premise check**, **Recommendation** with its evidence. Done when the recommendation names the evidence that decided it.
