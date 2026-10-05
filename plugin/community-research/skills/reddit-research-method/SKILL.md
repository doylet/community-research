---
name: reddit-research-method
description: >
  This skill should be used whenever Reddit is the source for research: "search Reddit for",
  "what do people on Reddit think", "find Reddit threads about", "pull the comments from this thread",
  or any use of the community-research tools search_subreddit and fetch_thread_comments. It sets the
  shared method for searching, sampling, quoting, citing and handling tool errors that the
  community-pulse, thread-digest, voice-of-customer, subreddit-discovery and competitive-research
  skills build on.
metadata:
  version: "0.1.0"
---

# Reddit Research Method

Apply this method to every Reddit research task. The workflow skills in this plugin add their own steps and output formats on top of it.

## The two tools

The `community-research` connector exposes two tools. Both return the same envelope: `{success, request_id, data, error, meta}`. Read `data` only when `success` is true.

**`search_subreddit(query, subreddit, limit, sort)`** finds posts.
- `subreddit`: name without `r/`. Always pass it explicitly, and pass `all` for a Reddit-wide search.
- `limit`: 1–100, default 25.
- `sort`: one of `relevance`, `hot`, `top`, `new`, `comments`. There is no time filter, so control recency with `sort=new` and by checking `created_utc`.
- Each result has `id`, `title`, `author`, `score`, `url`, `num_comments`, `created_utc` (Unix seconds), and `selftext` (only the first 500 characters).
- Results have no subreddit field. Read the subreddit from the `url` path (`reddit.com/r/<name>/comments/...`).

**`fetch_thread_comments(thread_id, max_comments)`** fetches one thread in full.
- `thread_id`: the alphanumeric ID only. From `reddit.com/r/x/comments/1abc2de/title/`, pass `1abc2de`. Short links like `redd.it/1abc2de` work the same way.
- `max_comments`: defaults to 2000. Pass 200–500 for a skim and leave the default for deep reads.
- The first row has `type: "post"` and holds the full post body. The rest have `type: "comment"` with `author`, `text`, `score`, `id`, `parent_id`, `created_utc` and `url`.
- A `parent_id` that starts with `t3_` is a top-level reply. One that starts with `t1_` is a reply to another comment. Use this to rebuild the conversation structure.

Detailed error handling is in `references/errors-and-limits.md`. Read it the first time a tool returns `success: false`.

## Search strategy

1. **Expand the query before searching.** Write 3–6 phrasings for one research question: the product or brand name, common misspellings and abbreviations, the problem in plain words ("can't export to excel"), comparison phrasings ("X vs Y", "alternative to X"), and feeling words ("frustrated with X", "love X").
2. **Search wide, then narrow.** Start with `subreddit=all` to see which communities come up, then search the 2–4 most relevant subreddits directly.
3. **Mix sorts.** `relevance` returns the strongest matches. `top` returns the threads with the most upvotes. `new` returns recent threads, which matters for anything time-sensitive. `comments` returns the threads with the most discussion.
4. **Deduplicate by `id`** across all searches before choosing threads.
5. **Choose threads to fetch** by relevance first, then discussion (`num_comments`), then recency. Fetch 5–10 threads for a normal question and up to 20 for a deep one. Don't fetch threads with fewer than ~5 comments unless the post itself is the evidence.
6. **Make independent calls in parallel** when the client allows it, for example the searches for each phrasing, or fetches for threads that are already chosen.

## Reading and weighting evidence

- Treat `score` as a sign of agreement within that community, not a measure of truth or popularity in general. Compare scores within a thread, not across subreddits of different sizes.
- Give more weight to comments that describe direct experience ("we switched last year and…") than to comments that only state an opinion.
- Note deleted or removed content (`[deleted]`, `[removed]`) without guessing what it said.
- Watch for promotional posts, affiliate links, and brand or employee accounts. Flag them and don't count them as user sentiment.
- Convert `created_utc` to a date and report the time span the evidence covers. Flag anything older than ~2 years as possibly out of date.

## Quoting and citation rules

- Copy quotes exactly from `text`. Trim with `…` but never paraphrase inside quotation marks.
- Cite every claim with a link: the comment or post `url`, or the thread `url` from search results.
- Attribute quotes to `u/<author>` only if the user wants usernames. By default, use "a commenter in r/<subreddit>". Never collect or profile individual users.
- Separate what the evidence shows from your interpretation. Label the interpretation.

## Honest limits to state in every report

- Reddit is a skewed sample. People who post there tend to be more technical, more vocal, and more often unhappy than typical users. Say so whenever findings could be read as market-wide.
- Search covers only what Reddit's search returns. It is not exhaustive and may miss older threads.
- Give the numbers the findings rest on: searches run, threads read, comments analysed, and the date range.

## Saving outputs

When the user asks for a file, or the analysis covers more than ~10 threads, offer to save:
- a Markdown report with the synthesis, and
- a CSV of the evidence (`theme, quote, subreddit, score, date, url`) so the quotes can be checked or reused.
