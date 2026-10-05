# Community Research plugin

Reddit research skills for Claude Desktop and Cowork, for researchers, product managers and product marketers. The plugin connects to the hosted Community Research MCP server and adds skills for running structured, cited research on Reddit discussions.

## Skills

| Skill | Use it for | Try saying |
|---|---|---|
| **community-pulse** | Themes and sentiment in one or more communities on a topic | "What is r/sysadmin saying about Copilot?" |
| **thread-digest** | A structured summary of one Reddit thread | "Digest this thread: https://reddit.com/r/…/comments/abc123/…" |
| **voice-of-customer** | Pain points, delights, feature requests and switching for a product | "Voice of customer report for Notion" |
| **subreddit-discovery** | Finding and ranking the subreddits where a topic is discussed | "Which subreddits talk about field service software?" |
| **competitive-research** | A product marketing comparison, battlecards and positioning gaps | "Compare Linear, Jira and Asana on Reddit and build battlecards" |
| **reddit-research-method** | Shared method (search strategy, quoting, citation, error handling) that the other skills use | Loads automatically |

Every report quotes Reddit comments exactly, links each claim to its source, and states its sample size, date range, and the limits of Reddit as a sample.

## Connector

The plugin's `.mcp.json` sets up one remote MCP server:

- **community-research**: `https://community-research-mcp.onrender.com/mcp` (streamable HTTP)
  - `search_subreddit(query, subreddit, limit, sort)`
  - `fetch_thread_comments(thread_id, max_comments)`

The server needs no credentials on your side, because the Reddit API credentials live on the hosted service. The service sleeps when idle, so the first call after a quiet period can take 30–60 seconds.

If you already added the `fetch-reddit` server with `install-claude-fetch-reddit.sh`, you can remove it after installing this plugin, so that Claude doesn't see two copies of the same tools.

## Building the .plugin file

From the repo root:

```bash
cd plugin/community-research && zip -r ../community-research.plugin . -x "*.DS_Store"
```

## Limits

- Search returns at most 100 posts per call, has no time filter, and gives only the first 500 characters of each post. The skills work around these limits by running several searches and fetching threads in full.
- No subscriber counts or user-history tools are available. Subreddit activity is estimated from search results.
- Reddit users are not a representative sample of all customers. The skills point this out in every report.
