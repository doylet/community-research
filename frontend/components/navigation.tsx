import Link from "next/link"

export function Navigation() {
  return (
    <nav className="border-b border-slate-800/80 bg-slate-950/90 backdrop-blur">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="font-semibold text-lg tracking-tight text-cyan-300">
            Community Research
          </Link>

          <div className="flex items-center space-x-6 text-sm sm:text-base">
            <Link href="/" className="text-slate-300 hover:text-white transition-colors">
              Search
            </Link>
            <Link href="/about" className="text-slate-300 hover:text-white transition-colors">
              About
            </Link>
            <a
              href="https://community-research-mcp.onrender.com/mcp"
              className="text-slate-300 hover:text-white transition-colors"
              target="_blank"
              rel="noreferrer"
            >
              MCP
            </a>
          </div>
        </div>
      </div>
    </nav>
  )
}
