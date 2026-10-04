import { CircleX, Info, RotateCw, SearchX, TriangleAlert, type LucideIcon } from "lucide-react"

import { formatNotificationDetails, type ApiNotification, type Severity } from "@/lib/api-errors"
import { cn } from "@/lib/utils"

const SEVERITY_STYLES: Record<Severity, { icon: LucideIcon; panel: string; accent: string }> = {
  info: {
    icon: Info,
    panel: "border-cyan-500/40 bg-cyan-950/30 text-cyan-50",
    accent: "text-cyan-300",
  },
  warning: {
    icon: TriangleAlert,
    panel: "border-amber-500/40 bg-amber-950/30 text-amber-50",
    accent: "text-amber-300",
  },
  error: {
    icon: CircleX,
    panel: "border-rose-500/40 bg-rose-950/30 text-rose-50",
    accent: "text-rose-300",
  },
}

export function ApiNotificationPanel({
  notification,
  retryHref,
}: {
  notification: ApiNotification
  retryHref?: string
}) {
  const style = SEVERITY_STYLES[notification.severity]
  const Icon = style.icon
  const details = formatNotificationDetails(notification)

  return (
    <section
      role={notification.severity === "error" ? "alert" : "status"}
      className={cn("mb-6 flex gap-4 rounded-2xl border p-6", style.panel)}
    >
      <Icon aria-hidden="true" className={cn("mt-0.5 h-6 w-6 shrink-0", style.accent)} />
      <div className="min-w-0 flex-1">
        <h2 className="mb-1 text-lg font-semibold text-white">{notification.title}</h2>
        {notification.message ? <p className="mb-1 break-words">{notification.message}</p> : null}
        <p className="text-slate-300">{notification.hint}</p>

        <div className="mt-4 flex flex-wrap items-center gap-4">
          {notification.retryable && retryHref ? (
            <a
              href={retryHref}
              className={cn(
                "inline-flex items-center gap-2 rounded-md border border-current px-3 py-1 text-sm hover:bg-white/5",
                style.accent,
              )}
            >
              <RotateCw aria-hidden="true" className="h-4 w-4" />
              Try again
            </a>
          ) : null}
          {details ? <code className="break-all text-xs text-slate-400">{details}</code> : null}
        </div>
      </div>
    </section>
  )
}

export function EmptyResultsNotice({ subreddit, query }: { subreddit: string; query: string }) {
  return (
    <section
      role="status"
      className="mb-6 flex gap-4 rounded-2xl border border-slate-800 bg-slate-900/50 p-6 text-slate-300"
    >
      <SearchX aria-hidden="true" className="mt-0.5 h-6 w-6 shrink-0 text-slate-400" />
      <div>
        <h2 className="mb-1 text-lg font-semibold text-white">No posts found</h2>
        <p>
          Nothing in r/{subreddit} matched &ldquo;{query}&rdquo;. Try a broader query or switch the sort mode.
        </p>
      </div>
    </section>
  )
}
