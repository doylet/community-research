import { ApiNotificationPanel, EmptyResultsNotice } from "@/components/api-notification"
import { classifyApiFailure, SEARCH_TIMEOUT_MS, type ApiNotification } from "@/lib/api-errors"
import { getApiBaseUrl } from "@/lib/endpoints"
import { cn } from "@/lib/utils"

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
  request_id: string
  data: RedditPost[] | null
  error: { code: string; message: string } | null
}

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

function isTimeout(error: unknown): boolean {
  return error instanceof DOMException && error.name === "TimeoutError"
}

const FORM_FIELDS =["subreddit", "query", "sort", "limit"] as const
type FormField = (typeof FORM_FIELDS)[number]

function searchQueryString(subreddit: string, query: string, sort: string, limit: number): string {
  return new URLSearchParams({
    subreddit,
    query,
    sort,
    limit: String(limit),
  }).toString()
}

// The API's INVALID_INPUT messages start with the offending parameter name.
function invalidFieldFor(notification: ApiNotification | null): FormField | null {
  if (notification?.code !== "INVALID_INPUT" || !notification.message) {
    return null
  }
  const firstWord = notification.message.split(/\s/, 1)[0]
  return FORM_FIELDS.find((field) => field === firstWord) ?? null
}

async function searchPosts(
  subreddit: string,
  query: string,
  sort: string,
  limit: number,
): Promise<{ posts: RedditPost[]; notification: ApiNotification | null }> {
  const apiBaseUrl = getApiBaseUrl()
  const context = { subreddit, apiBaseUrl }

  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}/api/search_posts?${searchQueryString(subreddit, query, sort, limit)}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(SEARCH_TIMEOUT_MS),
    })
  } catch (error) {
    const type = isTimeout(error) ? "timeout" : "network"
    return { posts: [], notification: classifyApiFailure({ type }, context) }
  }

  let payload: unknown = null
  try {
    payload = await response.json()
  } catch (error) {
    // The timeout also covers reading the body.
    if (isTimeout(error)) {
      return { posts: [], notification: classifyApiFailure({ type: "timeout" }, context) }
    }
    // Otherwise a non-JSON body (e.g. a gateway HTML page); classified by status below.
  }

  const envelope = payload as SearchResponse | null
  if (response.ok && envelope?.success && Array.isArray(envelope.data)) {
    return { posts: envelope.data, notification: null }
  }

  return {
    posts: [],
    notification: classifyApiFailure({ type: "http", status: response.status, body: payload }, context),
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

  const { posts, notification } = await searchPosts(subreddit, query, sort, limit)
  const invalidField = invalidFieldFor(notification)
  const fieldProps = (field: FormField) => ({
    "aria-invalid": invalidField === field || undefined,
    className: cn(
      "w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-cyan-400 focus:outline-none",
      invalidField === field && "border-amber-400",
    ),
  })

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
              {...fieldProps("subreddit")}
              placeholder="python"
            />
          </label>

          <label className="block md:col-span-2">
            <span className="mb-2 block text-sm text-slate-300">Query</span>
            <input
              name="query"
              defaultValue={query}
              {...fieldProps("query")}
              placeholder="llm prompt engineering"
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-sm text-slate-300">Sort</span>
            <select
              name="sort"
              defaultValue={sort}
              {...fieldProps("sort")}
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
              {...fieldProps("limit")}
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
        <span className="rounded-full border border-slate-700 px-3 py-1">Source: {getApiBaseUrl()}</span>
        <span className="rounded-full border border-slate-700 px-3 py-1">Results: {posts.length}</span>
        <span className="rounded-full border border-slate-700 px-3 py-1">Sort: {sort}</span>
      </section>

      {notification ? (
        <ApiNotificationPanel
          notification={notification}
          retryHref={`?${searchQueryString(subreddit, query, sort, limit)}`}
        />
      ) : null}

      {!notification && posts.length === 0 ? <EmptyResultsNotice subreddit={subreddit} query={query} /> : null}

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
                href={`${getApiBaseUrl()}/api/thread?thread_id=${post.id}`}
                target="_blank"
                rel="noreferrer"
                className="rounded-md border border-slate-700 px-3 py-1 text-slate-200 hover:bg-slate-800"
              >
                Inspect Thread JSON
              </a>
              <a
                href={`${getApiBaseUrl()}/search?id=${post.id}`}
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
