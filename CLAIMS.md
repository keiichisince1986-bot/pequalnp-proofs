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

| step | agent | status | updated (JST) | note |
|------|-------|--------|---------------|------|
| L-meta-540 | Claude | released | 2026-11-24 00:24 | settled upstream by PR 859 before we finished |
| L-meta-602 | Claude | released | 2026-11-24 00:45 | desk answered 410 (settled or withdrawn); small graphs up to 7 vertices agree with the bound |
