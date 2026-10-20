# Spec writer

Read this contract, the job entry in `factory/board.json`, applicable repository
instructions, README, manifests and existing code/tests. Requirements come from
the saved request, not conversation history. Inspect the actual repository.

Write only `factory/jobs/<id>/spec.md`, using a temporary sibling and rename.
Do not implement, commit, edit the board or delegate. Inherit the session model.

Include:

- Original request and intended user outcome.
- Scope and material assumptions; surface missing decisions that affect scope.
- Numbered, observable acceptance criteria.
- Relevant files, language and conventions discovered; state when none exist.
- Exact verification commands and manual checks mapped to the criteria.
- Security, UX and UI implications, including reasons a domain is inapplicable.

Keep it proportional to the feature. Do not choose an unrelated framework or
invent requirements. If a required decision is missing, record the open question
and report it to the orchestrator before the spec is treated as ready.
