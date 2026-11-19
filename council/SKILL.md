---
name: council
description: Council of models from different providers. Use before delegating research, grill, implement or review work, to staff each phase from .council.toml; for `council run` (grill to deploy); for `council decide` on a tradeoff.
argument-hint: "[run <idea|issue> | decide <question> | review <PR>]"
---

# Council

You are the **coordinator**: you staff each phase with **seats** (one model each, from distinct providers), brief them, verify what they return, and report. You are never a seat.

- `council run`: also read [pipeline.md](pipeline.md) and follow it.
- `[machines]` configured or `hc` installed: read [machines.md](machines.md) before launching.

## 1. Config

Merge `defaults.toml` (beside this file, documents every key), `~/.config/council/council.toml`, then `<repo>/.council.toml`; later wins per key.

A seat is `provider` or `provider:model`. The **provider** decides diversity: one seat per provider per phase, and in review the implementer's provider does not count. The **model** decides strength: resolve it through `[seats.<provider>] aliases`, `default` passes no model flag, anything else is a model ID.

## 2. Staff

Per phase, walk `prefer` and take the first `models` seats that can run. A seat that can't (CLI missing, not signed in, fails to start, in the machine's `skip`) is **absent: <reason>**. A phase short of seats stops here: report which are missing.

In review, the implementer's provider may add one **same-model review** seat: its confirmed findings count, its score and approval never do. With `skip_trivial`, a typo-sized task skips research and grill.

Done when every phase has its seats. Show the staffing in one table (phase, seats with models, machine) and proceed.

## 3. Brief

Every seat in a phase gets the same brief and nothing else: the independence is the point.

```text
You are one <phase> seat on a model council. <Read-only: change no files, start no agents. | Implement in this worktree only; start no agents.>
Task: <one sentence>
Where to look: <repo, branch/PR, files>
Context: <constraints, success criteria, known concerns>
Answer: position or result; evidence (file:line); biggest risk; what others may miss.
<review: findings instead, each with severity (blocker/major/minor/nit), file:line, evidence, fix; then Score N/10.>
End your final message with the full answer.
```

Use `jg` to fill **Where to look** when it is installed.

## 4. Launch

| Provider | Launch line | Gotcha |
| --- | --- | --- |
| claude | `claude --model <model> --disallowedTools Edit Write NotebookEdit Agent -- "<brief>"` | Pass `--model` every time. Implement seats drop `--disallowedTools`. Plan mode stalls on an approval prompt. |
| codex | `codex --no-daemon -s read-only [-m <model>] "<brief>"` | Implement: `-s workspace-write`. Read-only can't run `hc send`: read its screen. |
| grok | `grok [-m <model>] "<brief>"` | Read-only only by the brief. Trust dialog on a new folder. |
| gemini | `agy --mode auto --sandbox --model <model> -i "<brief>"` | Only its Gemini models. Without auto mode every command prompts: `skip` it on that machine. |

Without `hc`, run the lines as background processes with output to a file, in print mode (`claude -p`, `codex exec`, `grok -p`, `agy -p`), or run Claude seats as your own subagents.

## 5. Verify

- **research**: merge findings, mark disagreements.
- **grill**: answer what the code answers; ask the user the rest in one round.
- **implement** with `models` > 1: one worktree per seat, keep the attempt that wins on tests and review.
- **review**: give every finding a verdict against the code: **confirmed**, **rejected** (one-line reason) or **plausible** (listed, never blocks). Merge duplicates. Fix confirmed findings, re-review with fresh seats. Feature requests and unrelated refactors become follow-ups.

A review is **green** when every entry of `gate` passes: `evals` (every command exits 0, plus `final_evals` in the round that turns green), `findings` (nothing confirmed open at a `block_on` severity), `score` (every counting seat ≥ `min_score`). Done at green or `max_rounds`; then report what remains open.

## 6. Report

- PR: edit the description, before the model/harness line: a `## Council` section with the seats and one row per round (evals, confirmed findings per severity, rejected, scores). Write `absent` or `no score` where true; every number comes from a seat.
- Stop every seat you started.
- Say which machine and model each seat used, and which were absent.

## Decide

`council decide <question>`: one read-only round, every available provider (or the seats the user names). Write your own position first. Then one row per seat, **Consensus**, **Strongest dissent** (always shown), **Premise check**, **Recommendation** with its evidence.
