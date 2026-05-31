import Link from "next/link"

export function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 py-12 text-slate-300">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-3">
          <div>
            <h3 className="mb-4 text-lg font-bold text-cyan-300">Community Research</h3>
            <p className="text-slate-400">
              Find relevant conversations in Reddit communities and jump straight into thread-level analysis.
            </p>
          </div>

          <div>
            <h4 className="mb-4 font-semibold text-slate-100">Explore</h4>
            <ul className="space-y-2 text-slate-400">
              <li>
                <Link href="/" className="transition-colors hover:text-white">
                  Search Posts
                </Link>
              </li>
              <li>
                <Link href="/about" className="transition-colors hover:text-white">
                  About
                </Link>
              </li>
              <li>
                <a
                  href="https://community-research.onrender.com/health"
                  className="transition-colors hover:text-white"
                  target="_blank"
                  rel="noreferrer"
                >
                  API Health
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="mb-4 font-semibold text-slate-100">Tooling</h4>
            <ul className="space-y-2 text-slate-400">
              <li>
                <a
                  href="https://community-research-mcp.onrender.com/mcp"
                  className="transition-colors hover:text-white"
                  target="_blank"
                  rel="noreferrer"
                >
                  MCP Endpoint
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/doylet/community-research"
                  className="transition-colors hover:text-white"
                  target="_blank"
                  rel="noreferrer"
                >
                  Repository
                </a>
              </li>
              <li>
                <a
                  href="https://community-research.onrender.com/test"
                  className="transition-colors hover:text-white"
                  target="_blank"
                  rel="noreferrer"
                >
                  Reddit Connectivity Test
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-slate-800 pt-8 text-center text-slate-500">
          <p>&copy; {new Date().getFullYear()} Community Research.</p>
          <p className="mt-2 text-sm">Built for fast subreddit discovery and thread investigation.</p>
        </div>
      </div>
    </footer>
  )
}
