# VoC Coding Scheme

Tag each relevant comment with one or more codes. Use a sub-label after the colon to name the specific issue, for example `PAIN:pricing` or `REQ:offline-mode`.

| Code | Use when the comment… | Example |
|---|---|---|
| `PAIN` | describes a problem, frustration or limitation they have experienced | "Sync breaks every time I add a second device" |
| `DELIGHT` | praises a specific capability or outcome | "The API docs are the best I've used" |
| `REQ` | asks for, or wishes for, a capability | "If it had SSO we'd buy it tomorrow" |
| `CHURN` | says they left, or are about to leave, and why | "Cancelled after the price doubled" |
| `ADOPT` | says why they chose or switched to the product | "Moved from X because of the free tier" |
| `ALT` | names an alternative or competitor (record which one and the context) | "Just use Y, it does the same for half the price" |
| `WORKAROUND` | describes a hack used to get around a gap | "I export to CSV and fix it in Excel" |
| `SUPPORT` | describes an experience with support or the company | "Support took 3 weeks to reply" |
| `PRICE` | discusses price, value or plan structure | "Per-seat pricing kills it for small teams" |

## Severity for pain points

- **High:** blocks a core task, causes churn, or causes data loss, security exposure or a billing error.
- **Medium:** a recurring friction with a workaround, or one that slows adoption.
- **Low:** cosmetic, a rare edge case, or a matter of taste.

## Counting rules

- Count distinct comments, not upvotes. Report the highest score next to the count as a second signal.
- A comment that makes three separate complaints counts once for each code.
- Replies like "+1" or "same here" add to the count but are never quoted.
- Exclude promotional comments, and comments that appear to come from the vendor or a competitor's staff.
