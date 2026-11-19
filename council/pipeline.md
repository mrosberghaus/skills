# Council run: grill to deploy

**Experimental**: not yet run end to end. Report every step that doesn't work as written in the retro packet.

The user is present for preflight and grill, and does the retro. From the user's **go** until the retro packet the run is unattended: each question is answered from the code, docs and config, or handled by `[run] open_questions` (parked or assumed).

## Workflow skills

`[run] workflow = "builtin"`: use the built-in steps below. `"auto"`: for each step, use an installed skill when one matches, else the built-in step; `[run] steps` pins a skill per step key.

| Step key | Matches (e.g. Matt Pocock's skills) |
| --- | --- |
| `grill` | `grill-with-docs`, `grilling` |
| `prototype` | `prototype` |
| `spec` | `to-spec` |
| `tickets` | `to-tickets` |
| `implement` | `implement-spec`, `tdd` |
| `review` | `code-review` (that skill, never a same-named built-in) |
| `pr` | `pr` |
| `retro` | `retro` |

Find a skill in the session's skill list, else as `<dir>/**/<name>/SKILL.md` under `.agents/skills`, `~/.agents/skills`, `.claude/skills`, `~/.claude/skills`, or a plugin's `installPath` in `~/.claude/plugins/installed_plugins.json`. A skill that can't be invoked (e.g. `disable-model-invocation`): read its `SKILL.md` and follow it. After **go**, a skill's confirmation prompt counts as approved, except an open product or design question, which goes to `open_questions`.

## State and tracker

State lives where a fresh coordinator on the run machine finds it: the tracker, git (`feature/<slug>`, `ticket/<slug>-<n>`), and seat names `cr-<slug>-<phase>-<ticket|all>-r<round>-<provider>`. The **run log** (one entry per phase change) names the current phase and frontier; resume from it, and leave merged tickets merged.

`[run] tracker`:

- `local`: `.council/<slug>/` in the run machine's main checkout, listed in `.git/info/exclude`: `grill.md`, `spec.md`, `tickets/<n>-<title>.md` (`Status:`, `Blocked by:`, `Labels:` lines), `run-log.md`, `retro.md`. Seats get its absolute path.
- `github`, `gitlab`, `linear`: issues there; the run log is a comment on the spec issue.
- `repo`: whatever the repo documents.

## 0. Preflight (user present)

1. Config: defaults and user config (SKILL.md section 1).
2. Pick the run machine ([machines.md](machines.md)), clone or pull the repo there, then finish the config with the repo layer from the default branch.
3. Resolve the tracker (a remote one that isn't reachable: ask whether to use `local`; for `local`, create its folder) and the workflow skill per step.
4. Staff (SKILL.md section 2), including `[run] coordinator` and `[implement] merger`. Ticket worktrees will live under `<repo>-worktrees/`: create it, and for each implement provider launch once in a throwaway worktree there; the user accepts each trust dialog, then the throwaway worktree is removed. Launch each read-only seat once in the main checkout the same way. A provider that prompts again after that is dropped and the next in `prefer` tried.

Done when the user has seen, in one block: staffing with shortfalls, machine, workflow skill per step, tracker, the `[ship]` ceiling, `open_questions`, and **evals: none configured** if so.

## 1. Grill (user present)

Run the `[research]` seats first when the plan touches unfamiliar code; their findings feed the grill. Interview the user in rounds; recommend an answer to every question. New terms go to the repo's glossary (`GLOSSARY.md` unless it keeps one elsewhere), hard calls to ADRs (`docs/adr/` unless it keeps them elsewhere). Before round 1, add the `[grill]` seats' questions. With `[grill] prototypes = N`, `[implement]` seats build N throwaway variants of an open design question in scratch branches; the user keeps one, the rest are deleted.

Settle the **test seams**, the **ticket size**, and the ship behaviour: the grill can lower the `[ship]` ceiling (e.g. `auto` to `ready`), never raise it. Write all of it to the tracker as the grill record (`grill.md` for `local`), with the ship ceiling in the run log.

Before **go**, create `feature/<slug>` from the default branch (or from the kept prototype branch), commit the glossary and ADR changes to it, and push it.

With `hc` and a remote run machine, hand off after **go**: resolve `[run] coordinator` like any seat (fallback: the first available `[implement]` seat), then `hc run --bg --on <machine> --outlive-parent --name cr-<slug>-coordinator --cwd <repo> <its interactive line with the brief>`; the brief: "Use the council skill: continue council run `<slug>` at step 2 from `<tracker path or spec issue>`; report with hc send `<me>` at each phase change and when done or stuck." Otherwise continue in this session.

Done when the user said **go**, the grill record is written, `feature/<slug>` is pushed, and the handoff (if any) has reported its start.

## 2. Spec and tickets

- Spec in the glossary's terms, respecting ADRs, with the grill's seams; published to the tracker.
- Tickets as **tracer bullets**: vertical slices, one fresh session each, each naming its blockers, prefactoring first.
- The `[review]` seats check the breakdown once (size, blocking edges, gaps); apply every confirmed point, then publish the tickets with the `ready-for-agent` label (or the tracker's equivalent).

Open questions after **go**, per `[run] open_questions`: `park` gives the ticket the `needs-info` label and the question, its dependents wait, the rest continue. `assume` runs `council decide` and records the answer as an ADR marked `assumed: confirm in retro`.

Done when the spec and every ticket, with blockers, are published.

## 3. Implement

1. The **frontier** is every open ticket whose blockers are merged. Each frontier ticket gets an `[implement]` seat in its own worktree `<repo>-worktrees/<slug>-<n>` on `ticket/<slug>-<n>`, branched from the current `feature/<slug>`, at most `[implement] parallel` at a time; `[research]` seats explore first when the ticket needs it. The seat writes tests first at the agreed seams and commits; you push the ticket branch (sandboxed seats can't).
2. `evals` run in the ticket's worktree.
3. With `[review] per_ticket`, review seats run in the main checkout and read the ticket via `git diff feature/<slug>...ticket/<slug>-<n>` and `git show ticket/<slug>-<n>:<file>`, against the repo's coding standards and the ticket. The implementer seat gets the confirmed findings as a follow-up message (print mode: a fresh seat in the same worktree with the findings and the branch).
4. Green (or right after implementing when `per_ticket = false`): merges happen one at a time in a dedicated worktree `<repo>-worktrees/<slug>-merge` on `feature/<slug>`. The `[implement] merger` seat (fallback: the first available `[implement]` seat) merges the ticket, runs `evals`, and you push. A conflict it can't resolve, or red evals after the merge, returns the ticket to its implementer as another review round. Then close the ticket, remove its worktree, stop its seats, launch the new frontier.
5. At `max_rounds`: label the ticket `needs-info` with its open findings; its dependents wait.

Done when the frontier is empty (every ticket merged, labelled `needs-info`, or blocked by one), and no ticket worktree or seat remains.

## 4. Feature PR

With no merged ticket, skip to step 6. Otherwise open a **draft** PR from `feature/<slug>` to the default branch. Body: what changed (smallest sketch that shows it), evidence, merge danger (**door**: one-way when it can't be undone by a revert, like a migration or data deletion; else two-way; plus blast radius), the council section. Final review on the whole feature against its merge-base, with `evals` and `final_evals` in the merge worktree; a fresh `[implement]` seat there fixes confirmed findings. Any confirmed one-way finding makes the door one-way. Red CI is a blocker finding; a repo without CI reads **CI: none** and caps `merge` at `ready`.

Done when the gate and CI are green, or `max_rounds` is reached.

## 5. Ship

Enter only when every ticket is merged (none labelled `needs-info`), the final gate is green, CI is green, and no `assumed` ADR is open. Otherwise leave the PR as a draft and go to step 6.

Then `[ship]` decides, capped by every cap the run recorded (grill ceiling, not independent review, no CI, no `origin`):

- `merge = "ready"`: mark the PR ready for review. Done.
- `merge = "auto"`: mark it ready and merge it, except when the diff touches `.council.toml`, CI workflow files, or anything `deploy`/`verify`/`rollback` run, or the door is one-way and `one_way = "ready"`: then mark it ready only.
- After a merge, on a freshly pulled default branch: `deploy` (`"ci"`: wait for the deploy run; a command: run it), then `verify`. A failed deploy or verify runs `rollback` when set, then go to step 6.

A denied merge, push or deploy: go to step 6 and report it.

Done when the PR is ready or merged, and every deploy step that ran has a reported result.

## 6. Retro packet

Write it to the tracker (spec comment, or `retro.md` for `local`) and into the final message: spec, tickets, PR, seats per phase with shortfalls, findings per round with verdicts and reasons, Follow-ups, `needs-info` tickets with their questions, `assumed` ADRs, absent seats, what shipped. Then stop: the retro is the user's.

Done when the packet is written in both places and no seat of the run is running.
