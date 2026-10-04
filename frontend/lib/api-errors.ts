// Turns a failed API call into a user-facing notification.
// No path aliases or runtime imports: `node --test` loads this file directly.

export const SEARCH_TIMEOUT_MS = 45_000

export type Severity = "info" | "warning" | "error"

export type ApiNotification = {
  severity: Severity
  title: string
  message: string | null
  hint: string
  retryable: boolean
  status?: number
  code?: string
  requestId?: string
}

export type ApiFailureInput =
  | { type: "http"; status: number; body: unknown }
  | { type: "timeout" }
  | { type: "network" }

export type FailureContext = {
  subreddit: string
  apiBaseUrl: string
}

type NotificationTemplate = {
  severity: Severity
  title: string
  hint: (context: FailureContext) => string
  retryable: boolean
}

// Keys must cover every ErrorCode in app/errors.py (checked by tests/test_frontend_error_codes.py).
const ERROR_CODE_NOTIFICATIONS: Record<string, NotificationTemplate> = {
  INVALID_INPUT: {
    severity: "warning",
    title: "Check your search",
    hint: () => "Adjust the search and try again.",
    retryable: false,
  },
  NOT_FOUND: {
    severity: "warning",
    title: "Subreddit not found",
    hint: ({ subreddit }) => `Check the spelling of r/${subreddit}.`,
    retryable: false,
  },
  FORBIDDEN: {
    severity: "warning",
    title: "Subreddit is not accessible",
    hint: () => "It may be private, quarantined, or banned.",
    retryable: false,
  },
  UPSTREAM_RATE_LIMIT: {
    severity: "info",
    title: "Reddit is rate-limiting requests",
    hint: () => "Wait about a minute, then try again.",
    retryable: true,
  },
  UPSTREAM_UNAVAILABLE: {
    severity: "info",
    title: "Reddit is temporarily unavailable",
    hint: () => "Try again in a few moments.",
    retryable: true,
  },
  AUTH_CONFIGURATION_ERROR: {
    severity: "error",
    title: "Service configuration problem",
    hint: () => "This is not caused by your search. Report it with the request ID.",
    retryable: false,
  },
  INTERNAL_ERROR: {
    severity: "error",
    title: "Something went wrong on our side",
    hint: () => "Report it with the request ID.",
    retryable: false,
  },
}

const STATUS_FALLBACK_CODES: Record<number, string> = {
  400: "INVALID_INPUT",
  403: "FORBIDDEN",
  404: "NOT_FOUND",
  429: "UPSTREAM_RATE_LIMIT",
  502: "UPSTREAM_UNAVAILABLE",
  503: "UPSTREAM_UNAVAILABLE",
  504: "UPSTREAM_UNAVAILABLE",
}

type EnvelopeFields = {
  code?: string
  message: string | null
  requestId?: string
}

function readEnvelope(body: unknown): EnvelopeFields {
  if (typeof body !== "object" || body === null) {
    return { message: null }
  }
  const record = body as Record<string, unknown>
  const error = typeof record.error === "object" && record.error !== null ? (record.error as Record<string, unknown>) : {}
  return {
    code: typeof error.code === "string" ? error.code : undefined,
    message: typeof error.message === "string" && error.message.trim() ? error.message : null,
    requestId: typeof record.request_id === "string" ? record.request_id : undefined,
  }
}

export function classifyApiFailure(input: ApiFailureInput, context: FailureContext): ApiNotification {
  if (input.type === "timeout") {
    return {
      severity: "info",
      title: "The API is taking too long",
      message: null,
      hint: "It may be waking up. Try again in a few seconds.",
      retryable: true,
    }
  }

  if (input.type === "network") {
    return {
      severity: "error",
      title: "Could not reach the API",
      message: null,
      hint: `Check that the API is running at ${context.apiBaseUrl}.`,
      retryable: true,
    }
  }

  const envelope = readEnvelope(input.body)
  const knownCode = envelope.code && envelope.code in ERROR_CODE_NOTIFICATIONS ? envelope.code : undefined
  const templateCode = knownCode ?? STATUS_FALLBACK_CODES[input.status]
  const diagnostics = { status: input.status, code: envelope.code, requestId: envelope.requestId }

  if (templateCode) {
    const template = ERROR_CODE_NOTIFICATIONS[templateCode]
    return {
      severity: template.severity,
      title: template.title,
      message: envelope.message,
      hint: template.hint(context),
      retryable: template.retryable,
      ...diagnostics,
    }
  }

  return {
    severity: "error",
    title: `Unexpected response (HTTP ${input.status})`,
    message: envelope.message,
    hint: "Try again. If it keeps happening, report it.",
    retryable: input.status >= 500,
    ...diagnostics,
  }
}

export function formatNotificationDetails(notification: ApiNotification): string {
  const parts: string[] = []
  if (notification.status !== undefined) {
    parts.push(`HTTP ${notification.status}`)
  }
  if (notification.code) {
    parts.push(notification.code)
  }
  if (notification.requestId) {
    parts.push(`request ${notification.requestId}`)
  }
  return parts.join(" · ")
}
