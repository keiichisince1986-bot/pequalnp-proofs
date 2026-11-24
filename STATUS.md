# Status board: who is available, and how much budget each agent has left

Every agent keeps its own row up to date: when it starts or finishes a task, at least every 30
minutes while working, and at once when it hits a usage limit. Claude (the coordinator) reads this
board before assigning work in TASKS.md and moves work away from agents that are limited or low.

Budget column, one of:
- `ok` - no limit in sight
- `low (<what you can see>)` - a warning or a visible remaining amount, for example "about 20% of the 5-hour window left"
- `limited until <JST time>` - the tool refused or the plan's limit is reached; say when it resets if you can see it
- `unknown` - your tool shows nothing about usage

Write only what you can actually see; never guess a number.

| agent | updated (JST) | state | current task | budget | note |
|-------|---------------|-------|--------------|--------|------|
| Claude | 2026-11-24 18:18 | working | desk loop (Claude only): take step, prove, submit or release honestly, next | ok (weekly at warning; resets Wed 11:00) | continuous |
| Antigravity-Mac | 2026-11-24 18:21 | independent | coordination ended; works straight from join.txt (one step at a time) | - | - |
| Antigravity-Win | 2026-11-24 18:21 | independent | coordination ended; works straight from join.txt (one step at a time) | - | - |
| Muse | 2026-11-24 16:33 | off | owner turned Muse off; no leases held; do not assign | - | - |
| GPT | 2026-11-24 18:21 | independent | coordination ended; works straight from join.txt (one step at a time) | - | - |

Assignment rules used by Claude:
1. Lean proofs and submissions: Claude at night; in the day only short ones while Claude is `ok`.
2. CPU searches and independent re-checks: Antigravity-Mac first (fastest tools), then Antigravity-Win.
3. Desk steps during the day: GPT; if GPT is limited, Claude takes them only if `ok`.
4. An agent that is `limited` gets no new task; its doing tasks go back to todo after 60 minutes
   without an update (CLAIMS.md rule 2), so another agent can take them.
