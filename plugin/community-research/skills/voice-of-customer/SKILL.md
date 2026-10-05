---
name: voice-of-customer
description: >
  This skill should be used when the user wants customer feedback about a product, brand or category
  from Reddit, for example "voice of customer for X", "what do users complain about with X", "pain
  points with X", "feature requests for X on Reddit", "why do people leave X", "what do customers love
  about X", or "VoC report on X". It produces a voice-of-customer report covering pain points, delights,
  feature requests, alternatives and switching triggers, each backed by quotes and frequency.
metadata:
  version: "0.1.0"
---

# Voice of Customer

Collect what real users say about a product on Reddit and turn it into a voice-of-customer (VoC) report that a product team can act on.

Follow the **reddit-research-method** skill for tool use, sampling, quoting and limits. Use the coding scheme in `references/voc-coding.md`.

## Inputs

- **Product** (required): name, plus any aliases or the company name.
- **Focus** (optional): one area (onboarding, pricing, mobile app) or a segment (admins, small businesses).
- **Your product?** (optional): if the user owns the product, frame the recommendations as product actions. Otherwise frame them as market insight.

## Workflow

1. **Build the query set.** Cover the product name, aliases, and these patterns:
   - complaints: "<product> problem", "<product> issue", "<product> sucks", "frustrated with <product>"
   - churn: "leaving <product>", "switched from <product>", "cancel <product>"
   - praise: "love <product>", "<product> worth it"
   - wishes: "<product> feature request", "wish <product>"
   - alternatives: "<product> alternative", "<product> vs"
2. **Search** `subreddit=all` first. Then search the product's own subreddit, if it has one, and 1–3 relevant category subreddits. Use `relevance` and `new`. Deduplicate.
3. **Select 8–20 threads,** with a mix of complaint, praise and comparison threads. Note that a product's own subreddit tends to be more positive and more about support issues than general subreddits.
4. **Fetch and code.** Tag each relevant comment with one or more codes from `references/voc-coding.md`. Track the count of distinct comments per code, the highest score, and the 2–3 best quotes.
5. **Rank** pain points by how often they come up and how severe they are. Severe means it blocks a task, causes churn, or loses data or money.
6. **Write the report** in the format below.

## Output format

```markdown
# Voice of customer: <product>
<N> threads · <M> comments coded · <subreddits> · <date range>

## Summary
<3–5 bullets: the biggest pain point, the biggest delight, the top churn trigger, the top request, the main alternative>

## Pain points (ranked)
| # | Pain point | Mentions | Severity | Example |
|---|---|---|---|---|
| 1 | ... | 14 | High: drives churn | "<quote>" ([link](<url>)) |

## What users value
<themes with quotes>

## Feature requests
<grouped requests, with mentions and quotes>

## Switching: to and from
- **Leaving for:** <competitor>: <why>, (n mentions)
- **Arriving from:** <competitor>: <why>

## Segments
<differences by user type or subreddit, if visible>

## Recommendations
<3–5 actions, each tied to evidence above>

## Method and caveats
```

Offer an evidence CSV (`code, quote, subreddit, score, date, url`) along with the report.
