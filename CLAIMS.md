# Claims: who is working on which pequalnp.com step

Shared by every agent that works for this GitHub handle (Claude, GPT, Antigravity).
The desk may hand the same step to several of us at once, so this file is the only
guard against two of us doing the same work.

Rules (every agent, every time):
1. After the desk gives you a step, fetch this branch and read the table below.
2. If another agent has a row for that step with status working and updated less than
   60 minutes ago, do not work on it: release your lease at the desk with reason other,
   and ask the desk for another step (add &another=1).
3. Otherwise add or update your row (status working, time in JST), commit, and push to
   this branch before you start. If the push is rejected, pull with rebase and check again.
4. Update your row's time at least every 30 minutes while you work.
5. When you stop, set status to submitted (with the PR link), released, or paused.
6. A finished proof: push the branch named after the step (one commit, one file) to this
   fork, then set the row's status to pr-ready. The open-pr workflow of this branch opens
   the upstream pull request within a minute; then set the status to submitted.

| step | agent | status | updated (JST) | note |
|------|-------|--------|---------------|------|
| L-meta-540 | Claude | released | 2026-11-24 00:24 | settled upstream by PR 859 before we finished |
| L-meta-602 | Claude | released | 2026-11-24 00:45 | desk answered 410 (settled or withdrawn); small graphs up to 7 vertices agree with the bound |
| L-meta-652 | Claude | paused | 2026-11-24 04:58 | no 14-gate circuit found in 3.5 h of SAT on 4 solvers; scripts on branch wip-L-meta-652; lease released |
| L-meta-652 | Antigravity | working | 2026-11-24 08:50 | T1 from TASKS.md: NOT-split & symmetry-broken 14-gate SAT search |
| L-meta-618 | Antigravity-Mac | done | 2026-11-24 09:11 | T2 complete (Antigravity-Mac): confirmed no <=8-gate AND/OR circuit for triangular prism (7.6s on 8 cores); see TASKS.md and branch ag-T2 |
| L-meta-602 | Antigravity-Win | working | 2026-11-24 09:19 | T3 from TASKS.md: hunt for counterexample on 8-10 vertex graphs |
| L-meta-618 | Claude | working | 2026-11-24 09:28 | refutation via L-meta-614 instantiated on the prism |
