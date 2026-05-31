export default function AboutPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
      <div className="mb-12 rounded-2xl border border-cyan-500/30 bg-slate-900/70 p-8">
        <h1 className="mb-3 text-4xl font-bold text-white">About Community Research</h1>
        <p className="text-lg text-slate-300">
          Community Research helps you discover important Reddit conversations quickly and move from high-level search
          to detailed thread analysis.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="mb-2 text-xl font-semibold text-white">What You Can Do</h2>
          <ul className="space-y-2 text-slate-300">
            <li>Search by subreddit and keyword query.</li>
            <li>Sort results by relevance, hot, top, new, or comments.</li>
            <li>Open any post in Reddit, inspect thread JSON, or export CSV.</li>
          </ul>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="mb-2 text-xl font-semibold text-white">How It Works</h2>
          <p className="text-slate-300">
            The frontend sends search requests to the production API. The API uses Reddit credentials server-side,
            handles retries, and returns structured records for post and comment analysis.
          </p>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 md:col-span-2">
          <h2 className="mb-2 text-xl font-semibold text-white">Who This Is For</h2>
          <p className="text-slate-300">
            Researchers, product teams, founders, and community leads who need to validate ideas with real conversations
            instead of assumptions.
          </p>
        </section>
      </div>
    </div>
  )
}
