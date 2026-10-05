---
name: competitive-research
description: >
  This skill should be used for competitive product marketing research using Reddit, for example
  "compare X vs Y on Reddit", "how do people talk about our competitors", "competitive analysis of X,
  Y and Z", "what do users say about <competitor>", "find positioning gaps against X", "battlecard for
  X from Reddit", "why do people choose X over Y", or "what messaging resonates in this category". It
  produces a competitive comparison with perception, strengths, weaknesses, switching drivers,
  language customers use, and positioning opportunities.
metadata:
  version: "0.1.0"
---

# Competitive Product Marketing Research

Compare how Reddit users see a set of competing products, and turn that into material for product marketing: positioning, messaging, battlecards and gaps.

Follow the **reddit-research-method** skill for tool use, sampling, quoting and limits. Use the frameworks in `references/pmm-frameworks.md` for the analysis and the battlecard format.

## Inputs

- **Products** (required): 2–5 products. Ask which one, if any, belongs to the user ("our product").
- **Category** (optional): the market they compete in, used for category-level queries.
- **Deliverable** (optional): a full comparison (default), battlecards, a positioning-gap analysis, or a messaging and language study.

## Workflow

1. **Query matrix.** For each product, search the name and aliases with "review", "worth it", "problems" and "alternative". For each pair, search "A vs B", "A or B", and "switched from A to B" in both directions. For the category, search "best <category>" and "<category> recommendation".
2. **Search** `subreddit=all` first, then the 2–4 subreddits where the category is discussed most (run **subreddit-discovery** first if they are unknown). Use `relevance`, `top` and `new`. Deduplicate.
3. **Select threads** with balance in mind. Include head-to-head comparison threads, single-product threads for each product, and "what should I use" recommendation threads. Recommendation threads are the most useful because they show which products people pick unprompted. Aim for 12–25 threads in total, and record how many cover each product, because uneven coverage skews the comparison.
4. **Fetch and code.** For each comment that mentions a product, record the product, the attribute discussed (price, ease of use, features, support, reliability, integrations, performance and so on), the direction (+/−), and any switching direction. Copy the exact phrases users use to describe each product and the problem.
5. **Count recommendations.** In recommendation threads, tally which product commenters recommend and the main reason given.
6. **Synthesise** using the frameworks in the reference file: a perception map, a strengths and weaknesses grid, switching drivers, the customer's vocabulary, and positioning gaps.
7. **Write the report** in the format below. If battlecards were requested, add one per competitor using the battlecard template.

## Output format

```markdown
# Competitive landscape on Reddit: <category>
Products: <A, B, C> · <N> threads (<n per product>) · <M> comments · <date range>

## Executive summary
<4–6 bullets: who leads in perception and why, the clearest weakness of each competitor, the biggest open gap>

## How each product is perceived
| Product | Known for | Praised for | Criticised for | Net tone |
|---|---|---|---|---|

## Head-to-head
<for each key pair: when people pick A, when they pick B, with quotes>

## Recommendations by the community
| Product | Times recommended | Main reason given |
|---|---|---|

## Switching drivers
<A → B: why (n); B → A: why (n)>

## Customer language
<phrases users use for the problem and for each product; suggest messaging that uses their words>

## Positioning opportunities
<unmet needs and weak spots in competitors that no product owns, each tied to evidence>

## Method and caveats
<coverage per product, subreddit bias, presence of vendor or affiliate posts>
```

When the user's own product is included, report its weaknesses as plainly as the competitors'. A softened competitive read is worse than none.
