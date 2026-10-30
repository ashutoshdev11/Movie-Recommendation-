# Phase 0: Planning and Specification

Goal: a reliable blueprint. No code, no installs, no downloads.

## Tasks
1. Inspect the workspace (non-destructive): existing files, Python version, OS, git availability.
2. Confirm or challenge each item in "Fixed decisions" of RULES.md, with reasons for any challenge.
3. Write `docs/spec.md`: objectives, scope, out-of-scope, functional and non-functional requirements.
4. Write `docs/architecture.md`: modules, responsibilities, interfaces (`fit`, `predict`, `recommend`), data flow.
5. Write `docs/evaluation_protocol.md`: split, leakage prevention, metrics with formulas, relevance, handling of users without relevant items, cold-start experiment design.
6. Write a risk register (risk, likelihood, impact, mitigation) in `docs/spec.md`.
7. Create `PROJECT_STATUS.md` updates and `docs/decisions.md` entries.
8. Check that phase files 1 to 5 are consistent with the spec; propose edits, do not silently change them.

## Acceptance criteria
- [ ] The four docs above exist and contain every listed section.
- [ ] The evaluation protocol states split proportions, relevance threshold, K values, seed, and the primary selection metric.
- [ ] The protocol names at least three leakage risks and how each is prevented (for example: similarity computed on all data, mean ratings computed on all data, tuning on test).
- [ ] Every metric has a written formula.
- [ ] Risk register has at least 8 entries, each with a mitigation.
- [ ] No source code, no installed packages, no downloaded data (verify via file listing).
- [ ] Any deviation from the fixed decisions is justified in `docs/decisions.md`.

## Audit checklist
Confirm each criterion by opening the documents; check the workspace for forbidden artifacts; check that nothing claims work that was not done.
