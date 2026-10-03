// Hostnames must match deploy/services.yaml (checked by tests/test_service_endpoints.py).
const DEFAULT_API_URL = "https://community-research.onrender.com"

// Read on the server at request time (not inlined at build like NEXT_PUBLIC_*),
// so changing the URL on Render only needs a restart. NEXT_PUBLIC_API_URL is a
// legacy fallback.
export function getApiBaseUrl(): string {
  const configured = process.env.COMMUNITY_RESEARCH_API_URL || process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL
  return configured.replace(/\/+$/, "")
}

export const MCP_ENDPOINT_URL = "https://community-research-mcp.onrender.com/mcp"
