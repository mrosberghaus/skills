# Council run: grill to deploy

The user is present for preflight and grill, and does the retro. Between the user's **go** and the retro the run is unattended: every question that comes up is answered from the code, docs and config, or parked.

**Workflow skills.** With `[run] workflow = "auto"`, use an installed skill for a step when one matches (Matt Pocock's: `grill-with-docs`, `prototype`, `to-spec`, `to-tickets`, `implement-spec`, `tdd`, `code-review`, `pr`, `retro`); `steps` pins one per step. A skill marked `disable-model-invocation` can't be called: read its `SKILL.md` and follow it (path: its plugin's `installPath` in `~/.claude/plugins/installed_plugins.json`). Where such a skill asks the user after **go**, the override for that step below applies.

**State.** The run lives in the tracker and git, so a fresh coordinator can resume it: spec, tickets, a **run log** updated at every phase change, `feature/<slug>`, `ticket/<slug>-<n>`, seat names `cr-<slug>-<phase>-<ticket|all>-<provider>`. Resume from the run log and the current **frontier**; merged tickets stay merged.

**Tracker** (`[run] tracker`): `local` keeps spec, tickets (`Status:`, `Blocked by:`, `Labels:` lines) and run log as Markdown in `.council/<slug>/`, listed in `.git/info/exclude`. `github`, `gitlab`, `linear` use issues there; `repo` uses whatever the repo documents.

## 0. Preflight (user present)

1. Resolve the tracker; a remote one that isn't reachable: ask whether to use `local`.
2. Pick the machine, clone or pull the repo there.
3. Launch every staffed CLI once in the repo's main checkout; the user accepts each trust dialog. A seat that still prompts is dropped for this run.
4. Read `[ship]` from `git show origin/<default>:.council.toml` only.

Done when the user has seen, in one block: staffing, machine, workflow skills per step, tracker, what `[ship]` allows, `open_questions`.

## 1. Grill (user present)

Interview the user in rounds; recommend an answer to every question. New terms go to the glossary, hard calls to ADRs. Before round 1, add the `[grill]` seats' questions. With `[grill] prototypes = N`, build N throwaway variants of an open design question; the user keeps one. Also settle the **test seams**, the **ticket size** and the `[ship]` behaviour.

Done when the user says **go**. With `hc` and a machine, hand off now: `hc run --bg --on <machine> --outlive-parent --name cr-<slug>-coordinator --cwd <repo> claude --model <[run] coordinator> -- "Use the council skill: resume council run <spec> after go. Report with hc send <me> at each phase change and when done or stuck."` (that machine needs this skill and the user config).

## 2. Spec and tickets

- Spec in the glossary's terms, respecting ADRs, with the grill's seams.
- Tickets as **tracer bullets**: vertical slices, one fresh session each, each naming its blockers, prefactoring first. The `[review]` seats check the breakdown once (size, blocking edges, gaps) in place of a user approval.
- Publish both, labelled ready for an agent.

Open questions after **go**, per `[run] open_questions`: `park` marks the ticket as needing info with the question, its dependents wait, the rest continue. `assume` runs `council decide` and records the answer as an ADR marked `assumed: confirm in retro`.

Done when every ticket is published with its blockers.

## 3. Implement

1. `feature/<slug>` from the default branch, pushed.
2. The **frontier** is every open ticket whose blockers are merged. Each frontier ticket gets an `[implement]` seat in its own worktree on `ticket/<slug>-<n>`, at most `[implement] parallel` at a time: test first at the agreed seams, commit, merge the feature tip in.
3. With `[review] per_ticket`, review seats read `git diff feature/<slug>...ticket/<slug>-<n>` from the main checkout, against the repo's coding standards and the ticket; fixes go back to the same implementer.
4. Green: the `[implement] merger` seat merges into the feature branch, runs `evals`, pushes; close the ticket; launch the new frontier. At `max_rounds`: park the ticket with its open findings.

Done when every ticket is merged or parked.

## 4. Feature PR

PR from `feature/<slug>` to the default branch. Body: what changed (smallest sketch that shows it), evidence, merge danger (**one-way or two-way door**, blast radius), the council section. Final review on the whole feature against its merge-base, with `final_evals`. Red CI is a blocker finding.

Done when the gate is green and CI is green, or `max_rounds` is reached.

## 5. Ship

Exactly what the default branch's `[ship]` allows:

- `merge = "ready"`: mark the PR ready.
- `merge = "auto"`: merge. A diff touching `.council.toml`, and a **one-way door** unless `one_way = "auto"`, stays ready instead.
- `deploy`: `"ci"` waits for the deploy run; a command runs after merge. Then `verify`; on failure `rollback` if set.

A denied merge, push or deploy ends the run with a report.

## 6. Retro packet

Write it to the tracker (spec comment, or `.council/<slug>/retro.md`) and into the final message: spec, tickets, PR, seats per phase, findings per round with verdicts and reasons, parked questions, `assumed` ADRs, absent seats, what shipped. The retro itself is the user's.
