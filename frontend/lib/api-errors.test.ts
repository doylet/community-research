import assert from "node:assert/strict"
import { describe, it } from "node:test"

import { classifyApiFailure, formatNotificationDetails, type ApiNotification } from "./api-errors.ts"

const context = { subreddit: "python", apiBaseUrl: "http://localhost:8001" }

function envelope(code: string, message: string, requestId = "req-123") {
  return { success: false, request_id: requestId, data: null, error: { code, message }, meta: { retries: 0, version: "v1" } }
}

function classifyHttp(status: number, body: unknown): ApiNotification {
  return classifyApiFailure({ type: "http", status, body }, context)
}

describe("classifyApiFailure with known error codes", () => {
  const cases: Array<[string, number, ApiNotification["severity"], boolean, string]> = [
    ["INVALID_INPUT", 400, "warning", false, "Check your search"],
    ["NOT_FOUND", 404, "warning", false, "Subreddit not found"],
    ["FORBIDDEN", 403, "warning", false, "Subreddit is not accessible"],
    ["UPSTREAM_RATE_LIMIT", 429, "info", true, "Reddit is rate-limiting requests"],
    ["UPSTREAM_UNAVAILABLE", 503, "info", true, "Reddit is temporarily unavailable"],
    ["AUTH_CONFIGURATION_ERROR", 401, "error", false, "Service configuration problem"],
    ["INTERNAL_ERROR", 500, "error", false, "Something went wrong on our side"],
  ]

  for (const [code, status, severity, retryable, title] of cases) {
    it(`maps ${code}`, () => {
      const result = classifyHttp(status, envelope(code, `message for ${code}`))
      assert.equal(result.severity, severity)
      assert.equal(result.retryable, retryable)
      assert.equal(result.title, title)
      assert.equal(result.message, `message for ${code}`)
      assert.equal(result.status, status)
      assert.equal(result.code, code)
      assert.equal(result.requestId, "req-123")
    })
  }

  it("keeps the API message for invalid input", () => {
    const result = classifyHttp(400, envelope("INVALID_INPUT", "subreddit must contain letters, numbers, or underscores"))
    assert.equal(result.message, "subreddit must contain letters, numbers, or underscores")
  })

  it("names the subreddit in the not-found hint", () => {
    assert.match(classifyHttp(404, envelope("NOT_FOUND", "x")).hint, /r\/python/)
  })

  it("tells the user a configuration problem is not their fault", () => {
    assert.match(classifyHttp(401, envelope("AUTH_CONFIGURATION_ERROR", "x")).hint, /not caused by your search/)
  })

  it("classifies a 200 with success false by its code", () => {
    const fromOk = classifyHttp(200, envelope("NOT_FOUND", "Reddit resource was not found"))
    const from404 = classifyHttp(404, envelope("NOT_FOUND", "Reddit resource was not found"))
    assert.deepEqual({ ...fromOk, status: 404 }, from404)
  })
})

describe("classifyApiFailure without a usable envelope", () => {
  it("treats a 502 HTML page as upstream unavailable", () => {
    const result = classifyHttp(502, null)
    assert.equal(result.title, "Reddit is temporarily unavailable")
    assert.equal(result.status, 502)
    assert.equal(result.retryable, true)
    assert.equal(result.message, null)
    assert.equal(result.code, undefined)
  })

  it("falls back to status for 400, 403, 404, and 429", () => {
    assert.equal(classifyHttp(400, null).title, "Check your search")
    assert.equal(classifyHttp(403, null).title, "Subreddit is not accessible")
    assert.equal(classifyHttp(404, null).title, "Subreddit not found")
    assert.equal(classifyHttp(429, null).title, "Reddit is rate-limiting requests")
  })

  it("reports an unknown code as an unexpected response", () => {
    const result = classifyHttp(418, envelope("SOMETHING_NEW", "teapot"))
    assert.equal(result.title, "Unexpected response (HTTP 418)")
    assert.equal(result.message, "teapot")
    assert.equal(result.code, "SOMETHING_NEW")
    assert.equal(result.retryable, false)
  })

  it("makes an unexpected 5xx response retryable", () => {
    assert.equal(classifyHttp(507, null).retryable, true)
  })

  it("ignores malformed error fields", () => {
    const result = classifyHttp(500, { error: "boom", request_id: 7 })
    assert.equal(result.message, null)
    assert.equal(result.requestId, undefined)
  })
})

describe("classifyApiFailure without a response", () => {
  it("reports a timeout as the API waking up", () => {
    const result = classifyApiFailure({ type: "timeout" }, context)
    assert.equal(result.severity, "info")
    assert.equal(result.retryable, true)
    assert.match(result.hint, /waking up/)
    assert.equal(result.status, undefined)
  })

  it("names the API base URL on a network failure", () => {
    const result = classifyApiFailure({ type: "network" }, context)
    assert.equal(result.severity, "error")
    assert.equal(result.retryable, true)
    assert.match(result.hint, /http:\/\/localhost:8001/)
  })
})

describe("formatNotificationDetails", () => {
  it("joins status, code, and request ID", () => {
    const result = classifyHttp(429, envelope("UPSTREAM_RATE_LIMIT", "x", "3f2a9c1e"))
    assert.equal(formatNotificationDetails(result), "HTTP 429 · UPSTREAM_RATE_LIMIT · request 3f2a9c1e")
  })

  it("omits missing parts", () => {
    assert.equal(formatNotificationDetails(classifyHttp(502, null)), "HTTP 502")
    assert.equal(formatNotificationDetails(classifyApiFailure({ type: "network" }, context)), "")
  })
})
