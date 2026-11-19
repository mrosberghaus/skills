# Council run: grill to deploy

`council run <idea or issue>`. The user is present for **preflight + grill** and does the **retro**. Everything between runs unattended. Built on Matt Pocock's skills (plugin `mattpocock-skills`); this file maps his pipeline onto council seats and replaces his user gates.

## Matt's skills

Resolve his folder once: `installPath` of `mattpocock-skills@mattpocock` in `~/.claude/plugins/installed_plugins.json` on the coordinator's machine, then `<installPath>/skills/<area>/<name>/SKILL.md`. Most are `disable-model-invocation: true`, so never call them with the Skill tool: **read the file and follow it**, with the overrides below. Seat briefs say "read and follow `<path>`" too; Codex, Grok and agy have no Skill tool. "Code review" below means Matt's `engineering/code-review`, not any built-in skill of that name. If a file is missing (plugin renamed it), stop and report the path.

## State lives outside the session

Everything a restarted coordinator needs is in the tracker and git:

- spec issue (with a **run log** comment the coordinator updates at every phase change), tickets with their labels, feature branch `feature/<slug>`, ticket branches `ticket/<slug>-<n>`.
- terminal names are deterministic: `cr-<slug>-<phase>-<ticket|all>-<provider>`; `hc ls` shows what is still running.

On restart: read the run log, `hc ls`, `git branch -r`, continue from the current frontier. Never redo a merged ticket.

## 0. Preflight (attended)

1. `docs/agents/issue-tracker.md` exists in the repo. If not: tell the user to run `/setup-matt-pocock-skills` there, stop.
2. Pick the machine (SKILL.md "Where seats run"), clone or pull the repo there.
3. Clear every prompt while the user is here: launch each staffed CLI once in the repo's main checkout and have the user accept trust dialogs (`hc attach`). Codex's trust covers the repo root, so its worktrees too. A seat that still prompts is dropped for this run and reported.
4. Read `.council.toml` **from the default branch** (`git show origin/<default>:.council.toml`). `[ship]` counts only from this file, never from defaults or user config, and never from a branch the run produced.
5. Tell the user, in one block: staffing table, machine, what `[ship]` allows (stops at ready PR / merges / deploys), `open_questions` policy.

## 1. Grill (attended)

Follow `engineering/grill-with-docs` (it loads `grilling` + `domain-modeling`): glossary terms and ADRs get written as you go.

- Before round 1, send the plan to the `[grill]` seats (read-only, in parallel). Merge their questions into your first frontier. Ask nothing while they run.
- With `[grill] prototypes = N` and an open design question, follow `engineering/prototype`: N variants in the background, the user keeps one.
- Settle here what Matt's later skills would ask the user: **test seams** (`to-spec`), **ticket granularity** (`to-tickets`), and the `[ship]` behaviour above.
- The grill ends when the user says **go**. After that, never ask the user anything.

## 2. Spec and tickets (AFK)

- Follow `engineering/to-spec`. Override: skip "check with the user that these seams match"; use the seams from the grill.
- Follow `engineering/to-tickets`. Override: instead of "quiz the user", send the breakdown to the `[review]` seats for one read-only round (granularity, blocking edges, missing slices). Apply what holds up; no second round.
- Publish both to the configured tracker with the `ready-for-agent` label.

**Open questions** that turn up after **go**, per `[run] open_questions`:

- `park` (default): label the ticket `needs-info` (or the repo's equivalent), write the question on it; tickets it blocks wait, the rest continue. Listed in the final report.
- `assume`: run a `council decide` round on it, record the answer as an ADR marked `assumed: confirm in retro`, continue.

## 3. Implement (AFK)

Follow `engineering/implement-spec`, with council seats as its subagents:

- **Integration branch** = `feature/<slug>` from the default branch. Push it.
- **Implementer subagent** = an `[implement]` seat, one per frontier ticket, each in its own worktree on `ticket/<slug>-<n>` based on the feature branch. Brief: ticket pointer, spec pointer, "read and follow `engineering/tdd`", commit, merge the feature tip in, report. At most `[implement] parallel` at once.
- **Exploration subagent** = `[research]` seats when a ticket needs it.
- **Ticket review** (with `[review] per_ticket`): review seats read `git diff feature/<slug>...ticket/<slug>-<n>` from the main checkout (never the implementer's worktree) against `CODING_STANDARDS.md` and the ticket, following code review's two axes. Run the review gate (SKILL.md); fixes go back to the same implementer seat. Green → merge.
- **Merger subagent** = `[implement] merger` seat: merges the ticket branch into the feature branch, resolves conflicts, runs `evals`, pushes. Then close the ticket the way the tracker does, and launch the next frontier.
- A ticket stuck at `max_rounds`: label `needs-info` with the open findings, park its dependents, continue.

## 4. Feature PR (AFK)

1. Open the PR `feature/<slug>` → default branch. Body per `engineering/pr` (Summary, Evidence, Merge Danger with **Door** one-way/two-way and **Blast Radius**), plus the council table.
2. Final review gate on the whole feature, fixed point = merge-base with the default branch, including `final_evals`.
3. Wait for CI. Red CI is a blocker finding.

## 5. Ship (AFK, opt-in)

Only what the default branch's `.council.toml` `[ship]` allows:

- `merge = "ready"` (default): mark the PR ready, stop.
- `merge = "auto"`: merge when the gate is green and CI is green. Never auto-merge when the diff touches `.council.toml`, or when the PR is a **one-way door** (migration, data deletion) unless `one_way = "auto"`: leave those ready.
- `deploy = "ci"`: merging deploys; wait for that workflow and report its result. `deploy = "<command>"`: run it on the coordinator's machine after merge. Empty: no deploy.
- `verify = "<command>"`: run after deploy. On failure run `rollback` if set, else stop. Report either way.

Any denied merge, push or deploy: stop and report. Never work around it.

## 6. Retro (the user's)

Write a **retro packet** as a comment on the spec issue and in your final message: spec, tickets, PR, terminal names per phase, findings per round (confirmed / rejected, with reasons), parked questions, `assumed` ADRs, absent or dropped seats, what shipped. The user runs `/retro` on it (Matt's `engineering/retro`); don't run it yourself.

## Never

- Ask the user after **go**, or answer a seat's dialog for it.
- Substitute a seat, or let the implementer's provider count in its own review.
- Read `[ship]` from anywhere but the default branch's `.council.toml`.
