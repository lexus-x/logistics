# Session rules (Logistics)

Read at session start, in order: `README.md` → `MEMORY.md` (Open threads first) → top of `CHANGELOG.md`.
Read `PLAN.md` before touching anything in the detection study: it is the pre-registered protocol.

Before ending a session or after any meaningful change:
1. Add a dated entry to the top of `CHANGELOG.md` (what changed, files, runs launched or finished, results).
2. Record new decisions, numbers, gotchas in `MEMORY.md`; fix or delete entries that became wrong. Close or add Open threads.
3. If you add a script, data source or output, add it to `README.md`.

Rules:
- `PLAN.md` protocol items marked "pre-registered" or "fixed" are frozen. Don't change them. Log deviations in `MEMORY.md` with the reason.
- Never tune on the test splits (`test_id`, `test_ood`). Development uses `val` only.
- Secrecy: no cloud loggers (wandb/comet/hub), no git remote, no public hosts for data. Keep everything inside this folder.
- `runs/` and `data/` are expensive to rebuild. Never delete them without asking.
- `.kaggle/access_token` is a secret. Never print it or copy it anywhere.
