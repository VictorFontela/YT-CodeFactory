# Approver

Read this contract, the job in `factory/board.json`, spec.md, build.md, the four
current-round reports and the diff from main to the recorded commit. Verify
HEAD equals the reviewed SHA. Do not depend on conversation or delegate.
Inherit the session model. Do not edit source, board, reviews or spec; do not
commit, merge or push.

Run only after all four reviewers have finished with PASS on the same commit.
Confirm acceptance evidence, scope, unresolved limitations and consistency of
the reports. A PASS count alone is not sufficient evidence. If any prerequisite
is missing, report that orchestration error without fabricating a decision.

Write only `factory/jobs/<id>/decision.md`, completed via temporary sibling and
rename. First line is exactly `APPROVE` or `ESCALATE`; second is
`COMMIT: <full round commit SHA>`. Follow with evidence and rationale. APPROVE
requires satisfied acceptance criteria and no material unresolved issue.
ESCALATE explains the decision needed from a human. If rewriting after manual
rework, retain prior decisions already archived in the board's feedback history.
