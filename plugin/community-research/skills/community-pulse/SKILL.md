---
name: community-pulse
description: >
  This skill should be used when the user asks what a Reddit community thinks or is saying about a
  topic, for example "what is r/sysadmin saying about Copilot", "what's the sentiment on Reddit about X",
  "community pulse on Y", "how do people on Reddit feel about Z", "what are the main opinions on X on
  Reddit", or "summarise the Reddit discussion around this trend". It produces a themed synthesis
  with quoted evidence and links.
metadata:
  version: "0.1.0"
---

# Community Pulse

Report what one or more Reddit communities think about a topic. Group the findings into themes, back each theme with quoted evidence, and give a clear read on sentiment.

Follow the **reddit-research-method** skill for tool use, sampling, quoting and limits.

## Inputs

- **Topic** (required): what to take the pulse on.
- **Communities** (optional): specific subreddits. If none are named, find them first with a quick `subreddit=all` scan, or run the **subreddit-discovery** skill for broad or unfamiliar topics.
- **Time focus** (optional): "lately", "this year", "since the launch". Defaults to the full range, with recent threads given more weight.

If the topic is vague ("AI"), ask one clarifying question about the angle before searching.

## Workflow

1. **Plan.** Write 3–6 query phrasings and choose 2–4 target subreddits. State the plan in one line so the user can redirect it.
2. **Search.** In each target subreddit, run the phrasings with `sort=relevance`, then once with `sort=new` and once with `sort=top`. Use `limit=25`. Deduplicate by `id`.
3. **Select.** Pick 6–12 threads that cover a range: the most discussed, the most recent, and differing viewpoints. Don't fill the sample with near-duplicate threads.
4. **Fetch.** Pull each thread with `max_comments=500`. Use the full default only for one or two central threads.
5. **Code the evidence.** For each thread, note its stance and pull out distinct claims. Group the claims into 3–7 themes. For each theme, record:
   - the number of threads it appears in, and the rough share of comments that express it,
   - its overall direction (positive, negative, mixed or neutral),
   - the 2–3 strongest quotes, chosen for directness, upvotes and first-hand experience.
6. **Look for disagreement.** Find where the community is split, and where the most upvoted view differs from the most frequent one.
7. **Write the report** in the format below.

## Output format

```markdown
# Community pulse: <topic>
<communities> · <N> threads, <M> comments · <earliest date> to <latest date>

## Bottom line
<2–3 sentences: overall sentiment and the one thing to know>

## Themes
### 1. <Theme name>: <positive/negative/mixed>, <seen in N of M threads>
<1–2 sentence explanation>
> "<quote>" ([r/sub](<url>), <score> pts)
> "<quote>" ([r/sub](<url>), <score> pts)

...

## Where the community disagrees
<the split, with a quote from each side>

## What's changing
<recent shift, if any, from comparing the `new` threads with the `top` ones; otherwise say no clear shift>

## Sources
| Thread | Subreddit | Comments | Date |
|---|---|---|---|

## Caveats
<sample size, Reddit skew, gaps in search coverage>
```

Keep the report scannable. Use theme names that make a claim, such as "Pricing feels unfair after the seat change", not a label like "Pricing".
