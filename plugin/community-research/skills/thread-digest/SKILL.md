---
name: thread-digest
description: >
  This skill should be used when the user shares a Reddit thread link or ID and wants it understood,
  for example "summarise this Reddit thread", "digest this thread", "TL;DR this post", "what's the
  consensus in this thread", "what are people saying in <reddit url>", or "pull the key points from
  this discussion". It produces a structured digest: the post, the main positions, consensus and
  dissent, and the top quotes.
metadata:
  version: "0.1.0"
---

# Thread Digest

Turn one Reddit thread into a digest that someone can read in two minutes and trust.

Follow the **reddit-research-method** skill for tool use, quoting and citation.

## Workflow

1. **Get the thread ID.** Take it from the URL: the segment after `/comments/`, or the path of a `redd.it/` short link. If the user pasted only the ID, use it as given. If the link is a share link (`reddit.com/r/x/s/...`), ask for the full thread URL, because the tool can't resolve share links.
2. **Fetch** with `fetch_thread_comments(thread_id)`, using the default comment cap so the digest is complete. If several threads are given, fetch them in parallel and digest each one separately, then add a short cross-thread comparison.
3. **Rebuild the structure.** Comments whose `parent_id` starts with `t3_` are top-level. Group replies under their parents. Rank top-level comments by `score`.
4. **Analyse:**
   - What the original poster asked or claimed, and what context they gave.
   - The distinct positions or answers, each with a rough count of supporting comments and the highest score among them.
   - Consensus: what most top-voted comments agree on.
   - Dissent: well-supported minority views, and corrections of the post or of other comments.
   - Practical takeaways: specific recommendations, tools, numbers, workarounds or links people shared.
   - Whether the original poster came back with an update or resolution.
5. **Write the digest** in the format below.

## Output format

```markdown
# <Post title>
[r/<sub>](<post url>) · <date> · <N> comments analysed · post score <score>

**TL;DR:** <one or two sentences>

## What was asked
<2–3 sentences>

## Main positions
1. **<Position>**: <explanation> (≈<n> comments, top comment <score> pts)
   > "<quote>" ([link](<url>))
2. ...

## Consensus vs. dissent
- **Agreed:** ...
- **Disputed:** ...

## Useful specifics
- <tool, number, workaround or link that was mentioned>

## Resolution
<the original poster's update, or "No resolution posted">
```

For short threads (under ~20 comments), shorten the format to a TL;DR, the main positions and the best quotes. Don't pad the digest.
