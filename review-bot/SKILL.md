---
name: review-bot
description: Use when a `/grok review`, `/muse review`, `/claude review`, `/cursor review`, or `/codex review` comment is posted on a pull request in a watched repo, a review-bot watcher emits ACTION_REQUIRED, or the user runs /review-bot.
argument-hint: "[watch | <pr-number>] [--reviewer <name>]"
---

# Review bot

On-demand PR loop for a watched repo: review the diff, fix Critical and Important, tell the author what changed, **leave no worktree**.

**REQUIRED SUB-SKILLS:** requesting-code-review, receiving-code-review. Both must be available where the child runs — source: [obra/superpowers](https://github.com/obra/superpowers/tree/main/skills).
If a required sub-skill is unavailable, proceed with an ad-hoc review only, disclose the missing sub-skill in the summary, and propose `npx skills add obra/superpowers -s <name> -y` to install it.

Do not merge. Do not approve the PR. Do not fix Minors unless they are one-line and already in a file you are editing.

## Reviewer

The reviewer is defined by the CLI running this skill. Set `REVIEWER` once at the start of the run from your CLI's row — you know which CLI you are; do not guess from environment variables. If you genuinely cannot tell which CLI you are, see Invocation:

| CLI | REVIEWER | Trigger comment | Summary header |
|-----|----------|-----------------|----------------|
| Grok | `grok` | `/grok review` | `## Grok review` |
| Muse Code | `muse` | `/muse review` | `## Muse review` |
| Claude Code | `claude` | `/claude review` | `## Claude review` |
| Cursor | `cursor` | `/cursor review` | `## Cursor review` |
| Codex | `codex` | `/codex review` | `## Codex review` |

- A watcher `ACTION_REQUIRED` payload carries a `reviewer` field — that value is `REVIEWER` for the run.
- Otherwise `REVIEWER` comes from the invocation (see Invocation): your CLI's row by default, `--reviewer <name>` to override, or asked interactively when `/review-bot` is bare.
- If your CLI is not listed, use its lowercase session/binary name and follow the same conventions (`/<name> review`, `## <Name> review`).
- The capitalized form (`Grok`, `Muse`, …) goes in prose and headers; the lowercase form goes in trigger phrases, state paths, and script flags.
- One watcher per trigger phrase. `review-bot` with `grok` watches the same phrase as the standalone `grok-review` skill — run only one of them.

## Invocation

Parse trailing args as `[watch | <pr-number>] [--reviewer <name>]`:

| Invocation | Mode | Reviewer |
|------------|------|----------|
| `/review-bot` | ask: watch or one-shot (which PR?) | ask |
| `/review-bot watch` | watch | own CLI |
| `/review-bot 4345` | one-shot PR 4345 | own CLI |
| `/review-bot watch --reviewer muse` | watch | `muse` |
| `/review-bot 4345 --reviewer codex` | one-shot PR 4345 | `codex` |
| `/review-bot --reviewer muse` | ask: watch or one-shot (which PR?) | `muse` |

- Bare `/review-bot` asks for the reviewer name — offer your own CLI as the recommended default plus the known names — and for the mode (watch vs PR number) in the same round of questions. If you cannot ask (non-interactive run), fall back to your own CLI's reviewer in watch mode and say so.
- If you cannot determine which CLI you are, ask the user for the reviewer name before proceeding — even when the mode was given. Never guess the reviewer. In a non-interactive run where you cannot ask, stop and report that the reviewer is unknown instead of picking one.
- `watch` and `<pr-number>` are mutually exclusive; if both appear, ask which was meant.
- A `--reviewer` name outside the table is allowed when it is a sane lowercase name (letters, digits, `-`, `_`); trigger phrase, header, and state dir derive from it the same way.
- The override lasts for this run only.

## Done

A run is done only when all of these are true:

1. Reviewer findings exist (or an explicit empty-review note).
2. Every **verified** Critical and Important finding is fixed, committed, and pushed — or recorded as disagreed with a reason.
3. One PR comment is posted (template below). Trigger comment has a reaction.
4. The worktree this run created is **gone** (absent from the worktree list — see Cleanup).

Step 4 is a `finally`. Child crash, empty diff, push failure — still remove the worktree.

## Trigger

- Watcher `ACTION_REQUIRED` JSON, or `/review-bot <n>`.
- Issue comment whose first non-empty line is `/<REVIEWER> review` or `/<REVIEWER> review <focus>`.
- Author must be the watcher owner (the `gh`-authenticated login by default, `--author` overrides). Anyone else is ignored.
- Open PR only. Ignore repeats of a `databaseId` already handled.

## Orchestrator (this session)

Keep the main checkout on its current branch. Do the PR work in a child. One-shot (`/review-bot <n>`) has no payload: take the repo from the current checkout's origin; there is no trigger comment, so skip the reactions.

1. React `eyes` on the trigger comment (`<repo>` is the payload's `repo`):
   `gh api repos/<repo>/issues/comments/<id>/reactions -f content=eyes`
2. Spawn one isolated child for the PR, working in a fresh worktree off the checkout whose origin matches the payload's `repo`. Prompt: the Child section plus PR number, comment id, focus text, repo, and `REVIEWER`.
   - Grok: `spawn_subagent` with `general-purpose`, `isolation: "worktree"`, `background: true`.
   - Muse: `subagent_spawn` with `worktree_isolation: true` (or a `workflow` child with `isolation: true`).
   - Claude Code: `Agent` tool with `subagent_type: "general-purpose"`, `isolation: "worktree"` (worktree lands at `.claude/worktrees/agent-<agentId>`). It runs in the background — wait for the completion notification; its `<worktree>` block carries the `worktreePath` and `worktreeBranch` you clean up.
   - Cursor: start one background `cursor agent -w review-bot-<n> --workspace <checkout> -p --force "<prompt>"` shell process (worktree lands at `~/.cursor/worktrees/<reponame>/review-bot-<n>`); make the child run `pwd -P` first and return it as `worktree_path`, then wait for process exit.
   - Codex: start one background `codex exec --enable worktrees --worktree --json "<prompt>"` terminal process; make the child run `pwd -P` first and return it as `worktree_path`, then wait on the process with `write_stdin`.
3. Wait for the child (up to 30 min).
4. **Leave no worktree.** Use the child's `worktree_path` / worktree id and the Cleanup section. Confirm it is gone.
5. React `+1` on the trigger comment when the child posted the summary; `confused` if the child failed after you cleaned up.

One PR at a time. A second wakeup waits until the current child's worktree is gone.

## Child

Work only inside the isolated worktree. `REVIEWER` comes from the orchestrator prompt.

1. Attach the PR head without checking it out in the parent:
   ```bash
   gh pr checkout <n>
   ```
   Use `gh pr checkout`, never a raw `git fetch origin pull/<n>/head` + `git checkout -B <headRefName> origin/<headRefName>`: that fetch writes only `FETCH_HEAD` and never creates `origin/<headRefName>`, so the checkout succeeds only by luck on a same-repo PR (an earlier plain fetch had already mirrored the ref) and always fails on a fork PR. `gh pr checkout` creates the local branch and configures its push target, fork or not.
   If that branch is already bound to another worktree, `gh pr checkout <n> --detach`; step 5 then needs an explicit push target: `git push <head-remote> HEAD:<headRefName>`, with the head remote from `gh pr view <n> --json headRepositoryOwner,headRefName`.
2. Resolve the PR's real base — never hardcode `origin/main`:
   ```bash
   BASE_REF=$(gh pr view <n> --json baseRefName --jq .baseRefName)
   git fetch origin "+${BASE_REF}:refs/remotes/origin/${BASE_REF}"
   BASE_SHA=$(git merge-base "origin/${BASE_REF}" HEAD)
   HEAD_SHA=$(git rev-parse HEAD)
   ```
   A stacked PR targets another branch, not `main`, and `origin/main` then drags that base's whole divergence into the range — measured on a real one: 60 files in range against 5 actually changed. The reviewer reports findings in untouched code and step 5 pushes fixes for them. The explicit `+<ref>:refs/remotes/origin/<ref>` refspec matters for the same reason as step 1: a bare `git fetch origin <ref>` writes only `FETCH_HEAD`. Keep the `${BASE_REF}` braces — under zsh, an unbraced `$BASE_REF:refs/...` is parsed as the `:r` modifier and silently fetches a mangled ref.
3. **REQUIRED:** requesting-code-review against that range. PR title + body are the requirements. Reviewer is read-only.
4. **REQUIRED:** receiving-code-review on Critical and Important. Verify against this repo before editing. Skip Minors (list them). Push back in the summary when a finding is wrong.
5. If you changed files: conventional commit, `git push` (or `git push --force-with-lease` only after a rebase you started). Never `--force`. A fork PR without "Allow edits by maintainers" rejects the push — keep the findings, post the comment, and say the push was rejected under Remaining.
6. Post **one** PR issue comment with `gh pr comment <n> --body-file` (not a formal review). Do not put `/<REVIEWER> review` — or any other CLI's trigger phrase — in that body.

### Author comment

```markdown
## <Reviewer> review

Picked up `/<reviewer> review` from @<author>.
(If ad-hoc: "Ad-hoc review only — <name> was unavailable. Install: `npx skills add obra/superpowers -s <name> -y`.")

### Fixed
- <severity>: <what> (`<sha>` — `<path>`)
(or "Nothing pushed — no verified Critical/Important findings.")

### Remaining
- Minor: <path>: <issue>
- Skipped / disagreed: <issue> — <why>

### Assessment
Ready to merge: Yes | With remaining notes
<one sentence>
```

## Cleanup (non-negotiable)

Remove the worktree, then confirm it is gone:

- Grok: `grok worktree rm --force <id-or-path>`, confirm absent from `grok worktree list --json`. If `grok` fails, `git worktree remove --force <path>` from the source repo, then confirm again.
- Claude Code: `git worktree remove --force <worktreePath>` from the main checkout, confirm absent from `git worktree list`, then `git branch -D <worktreeBranch>` — removing the worktree leaves its branch behind. `ExitWorktree` does not apply: it only touches a worktree this session entered, never an `Agent` one.
- Cursor: `git worktree remove --force <worktree_path>` from the source repo, confirm absent from `git worktree list`, then `git branch -D <worktreeBranch>` if `-w` left a branch — ending the `cursor agent` process does not remove the worktree.
- Codex: `git worktree remove --force <worktree_path>` from the source repo, then confirm no exact `worktree <worktree_path>` record remains in `git worktree list --porcelain`; deleting the Codex session alone does not remove the worktree.
- Any other CLI: `git worktree remove --force <path>` from the source repo, confirm with `git worktree list`.

| Excuse | Reality |
|--------|---------|
| "Child will delete it" | Parent deletes. Child may be dead. |
| "Keep it for debug" | Log the path, then remove it. |
| "git worktree remove is enough" (Grok) | Prefer `grok worktree rm --force` so Grove tracking matches disk. |
| "Empty review, no worktree needed" | If you created one, remove it. |

Do not `grok worktree gc` or delete other sessions' worktrees.

## Watcher

Skill: `~/.agents/skills/review-bot/`. Script: `scripts/watch-review.py`.

State is per reviewer+repo: `~/.agents/plugin-data/<reviewer>-review/<owner>__<repo>/seen.json` (logs beside it under `logs/`; a legacy flat `seen.json` seeds the new path once). Each reviewer has its own trigger phrase, so watchers for different CLIs — or different repos — run side by side without double-handling. Never run two watchers on the same reviewer+repo: they share one `seen.json` and would race.

The script needs to know its reviewer: pass `--reviewer <name>` from the table above, or export `REVIEW_BOT_REVIEWER=<name>`. It refuses to run without one — a silent default would watch the wrong trigger phrase.

### Start (`/review-bot watch`)

1. Open your CLI in the checkout you want to watch. Prefer `main`, not a feature worktree.
2. Start the watcher with the resolved reviewer name (see Invocation):
   - Grok: run the script with `--reviewer grok --poll-interval 30` in the `monitor` tool with `persistent: true` (one monitor only). `/rename review-bot` and leave the session idle.
   - Claude Code: `CronCreate` with `cron: "*/3 * * * *"` and a prompt that runs the `--once` poll below, then starts a run per Orchestrator on each `ACTION_REQUIRED` line. Jobs are session-only (gone when the session exits), fire only while the REPL is idle, and recurring ones auto-expire after 7 days — re-create it when you restart the session.
   - Cursor: `/loop 3m In <checkout>, run python3 ~/.agents/skills/review-bot/scripts/watch-review.py --reviewer cursor --once; for each ACTION_REQUIRED line, follow Orchestrator.` Keep the session open.
   - Codex: run `/loop 3m In <checkout>, run python3 ~/.agents/skills/review-bot/scripts/watch-review.py --reviewer codex --once; for each ACTION_REQUIRED line, follow Orchestrator.` Keep the session open.
   - Any other CLI: schedule `--once` every 2–5 minutes (cron, `launchd`, or your scheduler of choice):

```bash
cd <checkout> && python3 ~/.agents/skills/review-bot/scripts/watch-review.py \
  --reviewer muse \
  --once
```

(`muse` above is an example — use the resolved reviewer name.) The repo is parsed from the `origin` remote of the cwd — run from the checkout you want to watch (`--repo owner/name` overrides auto-detect, `--repo-dir <path>` resolves origin elsewhere). The author defaults to the `gh`-authenticated login (`--author <login>` overrides). `--once` does one poll and exits 0; with existing state it prints `ACTION_REQUIRED` JSON for new trigger comments. Without `--once` the script polls forever (only useful while the session stays alive).
3. When a poll prints `ACTION_REQUIRED`, start a run per the Orchestrator section (its `reviewer` field is `REVIEWER`, its `repo` field is the target repo). Manual one-shot: `/review-bot 4345`.
