---
name: subreddit-discovery
description: >
  This skill should be used when the user needs to know where on Reddit a topic is discussed before
  researching it, for example "which subreddits talk about X", "where do <audience> hang out on Reddit",
  "find communities for X", "what subreddits should I monitor for X", or "map the Reddit landscape for
  this market". It produces a ranked list of subreddits with relevance, activity, tone and example
  threads.
metadata:
  version: "0.1.0"
---

# Subreddit Discovery

Find and rank the subreddits where a topic or audience actually shows up, so later research targets the right communities.

Follow the **reddit-research-method** skill for tool use and limits. There is no tool for subscriber counts, so judge relevance and activity from the search results themselves.

## Workflow

1. **Expand the topic** into 5–8 queries: product and category terms, the audience's job titles or identities ("sysadmin", "first-time founder"), problem phrasings, and adjacent tools.
2. **Search across Reddit.** Run each query with `subreddit=all`, `limit=100`, and alternate `sort=relevance` with `sort=new`. Collect every result.
3. **Group the results by subreddit.** Read the name from each `url` (`/r/<name>/`). For each subreddit, compute:
   - **Hits:** distinct matching posts.
   - **Discussion:** the median and maximum `num_comments` of those posts.
   - **Recency:** the share of hits from the last 12 months, and the date of the most recent hit.
   - **Spread:** how many different queries surfaced it. Broad spread means the topic is central to that community, not incidental.
4. **Probe the top candidates.** For the top 5–8 subreddits, run 1–2 queries directly in that subreddit to confirm the topic isn't just a single viral thread. If the subreddit returns `NOT_FOUND` or `FORBIDDEN`, record that.
5. **Characterise each one** from titles and post snippets: who posts there (practitioners, buyers, hobbyists, vendors), the tone (help-seeking, venting, news, promotional), and how relevant it is to the user's goal.
6. **Rank** by relevance first, then activity. Sort the subreddits into tiers:
   - **Core:** the topic is central and discussion is active. Research these first.
   - **Adjacent:** the topic comes up regularly as part of a broader focus.
   - **Long tail:** small or occasional, but sometimes high-signal.

## Output format

```markdown
# Where <topic> is discussed on Reddit
<N> queries · <M> posts scanned · <date>

## Core
| Subreddit | Hits | Median comments | Recent (12 mo) | Audience and tone | Example thread |
|---|---|---|---|---|---|
| r/... | 23 | 18 | 70% | Practitioners; help-seeking | [title](<url>) |

## Adjacent
...

## Long tail
...

## Recommended research plan
<which 2–4 subreddits to use for community-pulse, voice-of-customer or competitive-research, and the queries to run there>
```

End by offering to run **community-pulse** or **voice-of-customer** on the core subreddits.
