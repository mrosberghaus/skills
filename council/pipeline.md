# Council run: grill to deploy

`council run <idea or issue>`. The user is present for **preflight + grill** and does the **retro**. Everything between runs unattended.

Each step below says what must happen. **How** comes from a workflow skill when one is installed, otherwise from the built-in step written here. Nothing here requires a particular skill set.

## Workflow skills (optional)

`[run] workflow` picks the source:

- `auto` (default): for each step, use a matching installed skill if there is one, else the built-in step.
- `builtin`: always the built-in steps.
- a list of skill names per step, e.g. `steps = { spec = "to-spec", tickets = "to-tickets" }`, to pin them.

Known matches (Matt Pocock's `mattpocock-skills`, if installed):

| Step | Skill |
| --- | --- |
| grill | `grill-with-docs` (or `grilling`) |
| prototype | `prototype` |
| spec | `to-spec` |
| tickets | `to-tickets` |
| implement | `implement-spec`, `tdd` |
| review | `code-review` (his, not a built-in of the same name) |
| PR body | `pr` |
| retro | `retro` |

Find a skill in the session's skill list, or by path: `installPath` of its plugin in `~/.claude/plugins/installed_plugins.json`, then `<installPath>/skills/**/<name>/SKILL.md`. Skills marked `disable-model-invocation: true` can't be called with the Skill tool: **read the file and follow it**. Seat briefs say "read and follow `<path>`" too; non-Claude CLIs have no Skill tool. Wherever a workflow skill stops to ask the user after **go**, apply the override for that step below instead.

## Tracker

`[run] tracker`:

- `local` (default): spec, tickets and run log as Markdown files in `.council/<slug>/` of the repo's main checkout on the coordinator's machine (`spec.md`, `tickets/<n>-<title>.md` with `Status:`, `Blocked by:` and `Labels:` lines, `run-log.md`). Add `.council/` to `.git/info/exclude`, so it never lands in a commit or PR. Nothing leaves the machine.
- `github` / `gitlab` / `linear`: issues there, through `gh`, `glab` or the Linear tools.
- `repo`: whatever the repo documents (e.g. `docs/agents/issue-tracker.md`).

## State lives outside the session

A restarted coordinator needs only the tracker and git: the spec with a **run log** (a comment on the spec issue, or `run-log.md` for `local`) updated at every phase change, tickets with labels, branch `feature/<slug>`, ticket branches `ticket/<slug>-<n>`, and seat names `cr-<slug>-<phase>-<ticket|all>-<provider>`. On restart: read the run log, list running seats (`hc ls`, or the background processes), `git branch -r`, continue from the frontier. Never redo a merged ticket.

## 0. Preflight (attended)

1. Resolve the tracker. A remote tracker that isn't reachable (no `gh` auth, no Linear tools): say so and ask whether to use `local`.
2. Pick the machine (SKILL.md "Where seats run"); clone or pull the repo there.
3. Clear every prompt while the user is here: launch each staffed CLI once in the repo's main checkout; the user accepts trust dialogs (with `hc`: `hc attach <machine>/<name>`). Codex's trust covers the repo root and its worktrees. A seat that still prompts is dropped for this run and reported.
4. Read `.council.toml` **from the default branch** (`git show origin/<default>:.council.toml`). `[ship]` counts only from this file.
5. Tell the user in one block: staffing table, machine, workflow skills found per step, tracker, what `[ship]` allows, `open_questions` policy.

## 1. Grill (attended)

Interview the user until the plan is shared understanding: work the open decisions in rounds, recommend an answer for each, record new terms in the glossary and hard calls as ADRs where the repo keeps them (`GLOSSARY.md`, `docs/adr/`; create them if the repo has neither and the user agrees).

- Before round 1, send the plan to the `[grill]` seats (read-only, parallel); merge their questions into the first round. Ask nothing while they run.
- With `[grill] prototypes = N` and an open design question: N throwaway variants in the background, the user keeps one.
- Settle here what later steps would otherwise ask: **test seams**, **ticket granularity**, the `[ship]` behaviour.
- Ends when the user says **go**. After that, never ask the user anything.

## 2. Spec and tickets (AFK)

- **Spec**: problem, solution, user stories, implementation decisions, testing decisions (seams from the grill), out of scope. Use the glossary's terms; respect ADRs. Publish to the tracker.
- **Tickets**: vertical slices, each small enough for one fresh session, each listing the tickets that block it; prefactoring first. Instead of a user approval loop: one read-only round by the `[review]` seats (granularity, blocking edges, missing slices); apply what holds up. Publish, labelled ready for an agent.

**Open questions** after **go**, per `[run] open_questions`:

- `park` (default): mark the ticket as needing info, write the question on it; tickets it blocks wait, the rest continue. Listed in the final report.
- `assume`: `council decide` round, record the answer as an ADR marked `assumed: confirm in retro`, continue.

## 3. Implement (AFK)

- `feature/<slug>` from the default branch, pushed.
- The **frontier** is every open ticket whose blockers are merged. For each, one `[implement]` seat in its own worktree on `ticket/<slug>-<n>` from the feature branch, at most `[implement] parallel` at once. Brief: ticket and spec pointers, test first at the agreed seams, run the checks, commit, merge the feature tip in, report.
- `[research]` seats explore when a ticket needs it; findings go to a file the implementer is pointed at.
- **Ticket review** (`[review] per_ticket`): review seats read `git diff feature/<slug>...ticket/<slug>-<n>` from the main checkout, never the implementer's worktree, against the repo's coding standards and the ticket. Run the review gate (SKILL.md); fixes go back to the same implementer seat.
- Green → the `[implement] merger` seat merges into the feature branch, resolves conflicts, runs `evals`, pushes. Close the ticket the tracker's way; launch the new frontier.
- Stuck at `max_rounds`: mark the ticket as needing info with the open findings, park its dependents, continue.

## 4. Feature PR (AFK)

1. PR `feature/<slug>` → default branch. Body: what changed (smallest diagram or sketch that shows it), evidence (before/after, test runs), merge danger (**one-way or two-way door**, blast radius), the council table.
2. Final review gate on the whole feature, fixed point = merge-base with the default branch, including `final_evals`.
3. Wait for CI. Red CI is a blocker finding.

## 5. Ship (AFK, opt-in)

Only what the default branch's `.council.toml` `[ship]` allows:

- `merge = "ready"` (default): mark the PR ready, stop.
- `merge = "auto"`: merge when the gate and CI are green. Never auto-merge a diff that touches `.council.toml`, or a **one-way door** (migration, data deletion) unless `one_way = "auto"`: leave those ready.
- `deploy = "ci"`: merging deploys; wait for that run and report. `deploy = "<command>"`: run it after merge. Empty: no deploy.
- `verify = "<command>"` after deploy. On failure run `rollback` if set, else stop. Report either way.

Any denied merge, push or deploy: stop and report. Never work around it.

## 6. Retro (the user's)

Post a **retro packet** with the spec (issue comment, or `.council/<slug>/retro.md` for `local`) and in the final message: spec, tickets, PR, terminal names per phase, findings per round (confirmed / rejected, with reasons), parked questions, `assumed` ADRs, absent or dropped seats, what shipped. The user runs their retro on it; don't run it yourself.

## Never

- Ask the user after **go**, or answer a seat's dialog for it.
- Substitute a seat, or let the implementer's provider count in its own review.
- Read `[ship]` from anywhere but the default branch's `.council.toml`.
