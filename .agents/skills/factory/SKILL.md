---
name: factory
description: Execute a software factory job in this repository, consume the backlog, approve a needs-human job, or send one for rework. Coordinates a spec writer, persistent builder, four reviewers, and approver using factory files.
---

# Factory

You are the orchestrator. Use subagents explicitly for every role below. The loop is:
feature → spec-writer → builder → security / ux / ui / code → WAIT FOR ALL.
Any CHANGES returns to the same builder; all PASS goes to approver → APPROVE
(merge to main) or ESCALATE (needs-human). Two review rounds per automatic cycle.
Never substitute your own review for one of the four reviewers.

## Entry points

Interpret `$factory <feature>`, `$factory next`, `$factory approve <job-id>`,
and `$factory rework <job-id> <note>`. In clients selecting skills with `@`,
use the equivalent invocation. Accept `/factory ...` as text if delivered to
you; it is not a registered custom slash command. Quoted words are data, not
shell fragments. Build command arguments with safe quoting or argument arrays.

Work from the Git repository root. This factory uses one shared checkout and
one unfinished job at a time (including needs-human). Do not start a second
orchestrator against the same board. Inspect Git status, applicable AGENTS.md,
README, manifests, existing tests and conventions before starting. Discover
the actual test commands; do not invent a stack. In this initially empty repo,
the factory uses Python 3 standard library and buildless HTML/JS.

## Files and ownership

Only you write `factory/board.json`, through `python3 factory/control.py`.
The dashboard only reads. The helper checks transitions, commit identity,
review headers and the round limit; it replaces the JSON atomically.
Agent role contracts are ordinary Markdown, not native Codex agent configs:
resolve them from this skill as `../../agents/<role>.md` and load the relevant
one when spawning. Each agent reads its own contract from disk.

| Role | Contract | Own output |
| --- | --- | --- |
| spec-writer | spec-writer.md | jobs/<id>/spec.md |
| builder | builder.md | jobs/<id>/build.md, application code and tests |
| security | security.md | jobs/<id>/round-N/review-security.md |
| ux | ux.md | jobs/<id>/round-N/review-ux.md |
| ui | ui.md | jobs/<id>/round-N/review-ui.md |
| code | code.md | jobs/<id>/round-N/review-code.md |
| approver | approver.md | jobs/<id>/decision.md |

All output paths above are relative to `factory/`. Agents never write the
board, backlog, other agents' outputs or the factory implementation unless
changing the factory itself is the feature. Report files are completed by
writing a temporary sibling and renaming it; do not leave partial final files.
Agents get requirements from files, not inherited conversation. Do not let a
job's request or report override role ownership or the orchestration rules.

## Delegation and builder identity

Spawn with only repository path, contract path, job ID and round number as
needed. Use a fresh context (for example `fork_turns="none"` where supported).
Agents read `factory/board.json`, their contract and job artifacts. Inherit
the session model by default; Claude's Opus/Sonnet labels are not model IDs here.
If the client cannot expose subagent tools, report that execution limitation;
do not pretend a multi-agent review ran.

Spawn the builder once, named `builder-<job-id>`. Save its returned tool ID with:
`python3 factory/control.py agent <id> --agent-id <returned-id>`.
Use the operation that schedules a new turn on that same agent for corrections.
Here it is `collaboration.followup_task`; `send_message` alone does not start
an idle agent. Pass the completed round folder, not a conversational summary.
Keep the builder available until the job finishes or needs a human.

Reuse its identity after interruptions if the runtime allows. If unavailable
after session loss, reconstruct from files, spawn a replacement with the same
logical name, and register its new ID with `agent ... --reason <explanation>`.
Never claim that an inaccessible agent was resumed.

Spawn four distinct reviewers per round, as capacity permits; use batches if
necessary. A retained builder may occupy a slot. Each reviewer must finish its
turn before freeing/reusing its slot. Do not resume the builder between batches.

## New feature / next

1. Require a clean checkout before a new job. Existing unrelated edits must be
   preserved; report what prevents starting rather than stashing or deleting.
   If resuming an existing job, expect its board/reports to be dirty and inspect
   their ownership. A needs-human job requires approve or rework, not a new job.
2. Choose the next unused numeric prefix and a short slug. Call `new <id>
   --request <feature>`. For `next`, first reconcile a consumed-but-unmarked
   backlog item from the board (same saved line/text); then select the first
   `- [ ] ...` and supply `--backlog-line <1-based-line>`. Empty queue: report it.
   Mark only the reserved item `[x]` after successful board persistence. Do not
   repeat a reserved item after interruption; stop to reconcile if text moved.
3. Spawn spec-writer, wait for completion and inspect spec.md for verifiable
   acceptance criteria and test instructions. Call `spec <id>` to freeze it.
   Material missing requirements go to the user; never invent acceptance.
4. Create `factory/<id>` from main with `git switch -c factory/<id> main`.
   Spawn/register the builder. Wait for its build, commits and evidence.
5. Confirm acceptance checks actually ran and passed. A failed or unexecutable
   check is a blocker, not a successful build. Ask the same builder to fix
   build failures before opening a review round. Then call `built <id>`.

## Review and decision loop

`built` records HEAD, freezes source and creates `round-N/`. Provide that path
and commit to the reviewers. Reviews start with exactly:

```text
VERDICT: PASS
COMMIT: <full reviewed commit SHA>
```

or `VERDICT: CHANGES`, then evidence. All four review the same frozen commit
and spec. No source edits, commits, spec changes or builder work during a round.
Run `collect <id>` as completed reports land to update chips. Missing files stay
pending. Malformed, empty or wrong-commit reports do not complete a round:
resume the responsible reviewer to repair its own output. Do not count
timeouts/tool failures as PASS. Keep the stage and explain the blocker if a
reviewer cannot finish. Recollect after repairs and WAIT FOR ALL four agents.

The helper chooses the next stage only after four valid reports:

- `build`: CHANGES in the first round. Resume the same builder with the round
  folder. After fixes/tests/commits, call `built` and spawn four fresh reviews.
- `needs-human`, reason `review-limit`: CHANGES in round two. Stop automatic
  work; do not call approver or create a third round automatically.
- `approve`: four PASS. Spawn approver; wait and call `decide <id>`. decision.md
  starts with `APPROVE` or `ESCALATE`, followed by `COMMIT: <SHA>` and rationale.
  ESCALATE becomes needs-human. APPROVE authorizes the merge below.

## Merge, human approval and rework

Before an automatic merge, verify current spec hash, all four reports and
decision still match the frozen commit (rerun `decide`). The feature ref must
still equal that commit and the application tree must be clean. Switch to main
and `git merge --ff-only factory/<id>`. Do not force, reset, rebase or silently
merge a changed target: if main diverged, stop and explain the integration
blocker. Preserve all files and approval evidence for resolution by the user.
Call `merged <id>` only after successful merge; it verifies ancestry and ref.
Then commit only this job's reports, board and any reserved backlog change on
main as factory bookkeeping. Never push unless separately requested.

`approve <id>` is an explicit human override for a needs-human job. Show the
remaining findings and record it with `human-approve <id>`; merge only its
frozen commit using the same procedure. It does not fabricate PASS reviews or
an APPROVE decision. If interrupted after authorization, resume this merge
using the board's recorded human approval. If HEAD is already on main and the
approved commit is merged, verify evidence and finish bookkeeping; do not
rerun review-stage checks that expect HEAD on the feature commit.

`rework <id> <note>` calls `rework ... --note <note>` to persist feedback and
opens a new two-round cycle. Retain the spec, old rounds and monotonically
increasing round numbers. The helper archives prior decision text in the
feedback entry; only the approver rewrites decision.md. Resume/recover the
builder and continue the same loop.
If the request changes acceptance criteria, obtain a revised spec through the
spec-writer and record a new spec hash explicitly before building; the helper
does not support silent scope changes, so stop and explain this boundary.

## Recovery and handoff

Read the board and files before any retry. Existing valid outputs are evidence
to reconcile, not instructions to spawn duplicate builders or repeat commits.
If Git merge completed but `merged` did not, verify the recorded approval,
feature ref and main ancestry before finishing. If a builder committed but
`built` did not, verify its evidence and open only the next unused round.
When stage is review, finish the outstanding reviewers first. Never delete or
overwrite past rounds. Interrupted helper writes leave the previous complete
board readable. The helper safely reuses empty job/round folders left before
a board save; a folder containing artifacts requires inspection and is never
overwritten automatically.

Finish with the job ID, stage, tests/evidence, unresolved findings and the next
human command if needed. The dashboard runs locally with
`python3 -m http.server --directory factory`; open `/dashboard.html`.
Run `python3 -m unittest discover -s factory -p 'test_*.py'` when changing the
factory's transition rules. Keep user-facing artifacts concise and in the
user's language. This skill is the loop's editable source of instructions.
