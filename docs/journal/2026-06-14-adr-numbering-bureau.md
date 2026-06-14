# Untangling ADR numbers under parallel efforts

Session record, 2026-06-14. A day of many concurrent worktrees surfaced a latent flaw in how decision records get their
numbers, and ended with a fix for it.

## What happened

It started as a small repair: two records both numbered 0023 — a set-valued-field decision and a field-colour one. They
were genuinely distinct decisions that had each grabbed the next free number off their own branch base and collided on
main. The colour record was the later decision and carried every inbound reference (`theme.py`, `cli.py`, the list
tests, ADR 0016), so it took the new number; the genres record kept 0023. That landed as
[ADR 0024](../decisions/0024-a-field-colour-vocabulary.md).

But the duplication was a symptom, not the bug. A survey of the live worktrees showed the same failure spreading:
`claim-registry`, `swedish-sort-order`, and the just-landed colour record all held 0024, and 0025/0026 were spoken for
on other branches. An ADR number is a name from a single global sequence, handed out by parallel branches that cannot
see each other until they land — so collisions were inevitable, not unlucky.

## The fix, and a fitting last collision

The resolution is [ADR 0030](../decisions/0030-claim-record-numbers-from-a-bureau.md): a numbering bureau in the shared
common git dir (`$GIT_COMMON_DIR/info/adr-numbers/`), where `just adr-new <slug>` allocates a number that every worktree
of the clone can see, that is never committed and so never merge-conflicts. The design moved through three readings in
conversation — assign-at-land, scan-all-branches, and finally registry-as-sole-authority — before settling on the last:
the bureau alone says what is allocated, numbers are permanent, and land stays dumb.

The bureau branch then became the day's final casualty of the very bug it fixes. While it waited to land,
`0027-sort-and-match-in-the-users-locale` landed on main, colliding with its own 0027. It was renumbered to 0030 by hand
— the bureau prevents future collisions but cannot heal the ones that predate it — and the local registry was seeded
from main so the next allocation lands at 0031.

## Lesson

The pre-bureau in-flight numbers still need reconciling by hand as those branches land. From here, every record born
through `just adr-new` is collision-free by construction. The general shape — when independent parties must agree on a
name, give them one place they can all see rather than hoping they guess the same next value — is worth remembering the
next time leeks grows a shared sequence.
