type SearchParams = {
  subreddit?: string | string[]
  query?: string | string[]
  sort?: string | string[]
  limit?: string | string[]
}

type RedditPost = {
  id: string
  title: string
  author: string
  score: number
  url: string
  num_comments: number
  created_utc: number
  selftext: string
}

type SearchResponse = {
  success: boolean
  data: RedditPost[] | null
  error: { message: string } | null
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://community-research.onrender.com"
const VALID_SORTS = new Set(["relevance", "hot", "top", "new", "comments"])

function getStringParam(value: string | string[] | undefined, fallback: string): string {
  if (typeof value === "string" && value.trim()) {
    return value.trim()
  }
  return fallback
}

function clampLimit(value: string | string[] | undefined): number {
  const parsed = Number.parseInt(typeof value === "string" ? value : "", 10)
  if (Number.isNaN(parsed)) {
    return 12
  }
  return Math.min(Math.max(parsed, 1), 100)
}

function formatUtc(createdUtc: number): string {
  return new Date(createdUtc * 1000).toLocaleString()
}

async function searchPosts(subreddit: string, query: string, sort: string, limit: number): Promise<{ posts: RedditPost[]; error: string | null }> {
  const params = new URLSearchParams({
    subreddit,
    query,
    sort,
    limit: String(limit),
  })

  try {
    const response = await fetch(`${API_BASE_URL}/api/search_posts?${params.toString()}`, {
      cache: "no-store",
    })

    if (!response.ok) {
      return { posts: [], error: `Search failed with status ${response.status}.` }
    }

    const payload = (await response.json()) as SearchResponse
    if (!payload.success || !payload.data) {
      return { posts: [], error: payload.error?.message ?? "Search failed." }
    }

    return { posts: payload.data, error: null }
  } catch {
    return { posts: [], error: "Could not reach the API service." }
  }
}

export default async function HomePage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>
}) {
  const resolvedParams = await (searchParams ?? Promise.resolve({} as SearchParams))
  const subreddit = getStringParam(resolvedParams.subreddit, "python")
  const query = getStringParam(resolvedParams.query, "agentic workflows")
  const requestedSort = getStringParam(resolvedParams.sort, "top")
  const sort = VALID_SORTS.has(requestedSort) ? requestedSort : "top"
  const limit = clampLimit(resolvedParams.limit)

  const { posts, error } = await searchPosts(subreddit, query, sort, limit)

  return (
    <div className="max-w-6xl mx-auto px-4 py-10 sm:px-6 lg:px-8">
      <section className="mb-8 rounded-2xl border border-cyan-500/30 bg-slate-900/70 p-8 shadow-[0_0_60px_rgba(34,211,238,0.12)]">
        <p className="mb-2 text-xs uppercase tracking-[0.2em] text-cyan-300">Reddit Intelligence</p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">Search Communities, Not Guesswork</h1>
        <p className="max-w-3xl text-slate-300">
          Run targeted subreddit searches and open thread-level records directly from one place. Results are live from
          the production API.
        </p>
      </section>

      <section className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <form className="grid gap-4 md:grid-cols-5" method="get">
          <label className="block md:col-span-1">
            <span className="mb-2 block text-sm text-slate-300">Subreddit</span>
            <input
              name="subreddit"
              defaultValue={subreddit}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-cyan-400 focus:outline-none"
              placeholder="python"
            />
          </label>

          <label className="block md:col-span-2">
            <span className="mb-2 block text-sm text-slate-300">Query</span>
            <input
              name="query"
              defaultValue={query}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-cyan-400 focus:outline-none"
              placeholder="llm prompt engineering"
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-sm text-slate-300">Sort</span>
            <select
              name="sort"
              defaultValue={sort}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-cyan-400 focus:outline-none"
            >
              <option value="relevance">relevance</option>
              <option value="hot">hot</option>
              <option value="top">top</option>
              <option value="new">new</option>
              <option value="comments">comments</option>
            </select>
          </label>

          <label className="block">
            <span className="mb-2 block text-sm text-slate-300">Limit</span>
            <input
              name="limit"
              type="number"
              min={1}
              max={100}
              defaultValue={limit}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-cyan-400 focus:outline-none"
            />
          </label>

          <button
            type="submit"
            className="rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-950 transition hover:bg-cyan-300 md:col-span-5"
          >
            Search Reddit
          </button>
        </form>
      </section>

      <section className="mb-6 flex flex-wrap gap-3 text-sm text-slate-400">
        <span className="rounded-full border border-slate-700 px-3 py-1">Source: {API_BASE_URL}</span>
        <span className="rounded-full border border-slate-700 px-3 py-1">Results: {posts.length}</span>
        <span className="rounded-full border border-slate-700 px-3 py-1">Sort: {sort}</span>
      </section>

      {error ? (
        <section className="rounded-2xl border border-rose-500/40 bg-rose-950/30 p-6 text-rose-100">{error}</section>
      ) : null}

      {!error && posts.length === 0 ? (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 text-slate-300">
          No posts found. Try a broader query or switch the sort mode.
        </section>
      ) : null}

      <section className="space-y-4">
        {posts.map((post) => (
          <article key={post.id} className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5">
            <div className="mb-3 flex flex-wrap items-center gap-3 text-xs text-slate-400">
              <span className="rounded-full bg-slate-800 px-2 py-1">u/{post.author || "unknown"}</span>
              <span>Score {post.score}</span>
              <span>{post.num_comments} comments</span>
              <span>{formatUtc(post.created_utc)}</span>
            </div>

            <h2 className="mb-3 text-xl font-semibold text-white">{post.title}</h2>

            {post.selftext ? <p className="mb-4 line-clamp-4 text-slate-300">{post.selftext}</p> : null}

            <div className="flex flex-wrap gap-3 text-sm">
              <a
                href={post.url}
                target="_blank"
                rel="noreferrer"
                className="rounded-md border border-cyan-400/40 px-3 py-1 text-cyan-300 hover:bg-cyan-400/10"
              >
                Open on Reddit
              </a>
              <a
                href={`${API_BASE_URL}/api/thread?thread_id=${post.id}`}
                target="_blank"
                rel="noreferrer"
                className="rounded-md border border-slate-700 px-3 py-1 text-slate-200 hover:bg-slate-800"
              >
                Inspect Thread JSON
              </a>
              <a
                href={`${API_BASE_URL}/search?id=${post.id}`}
                target="_blank"
                rel="noreferrer"
                className="rounded-md border border-slate-700 px-3 py-1 text-slate-200 hover:bg-slate-800"
              >
                Download CSV
              </a>
            </div>
          </article>
        ))}
      </section>
    </div>
  )
}
