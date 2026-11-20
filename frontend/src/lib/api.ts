// Base URL of the FastAPI backend. Override with NEXT_PUBLIC_API_URL in .env.local.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

/** Turn FastAPI's error body into one readable sentence. */
function errorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg); // 422 validation
  return `Request failed (${status})`;
}

/**
 * Call the backend. Always sends the session cookie (credentials: "include").
 * Throws ApiError on non-2xx responses, or status 0 if the backend is unreachable.
 */
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        // JSON bodies are strings; FormData (file uploads) sets its own multipart header.
        ...(typeof init.body === "string" ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError(0, `Can't reach the AutoGuardian server at ${API_URL}`);
  }

  if (response.status === 204) return undefined as T;
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, errorMessage(body, response.status));
  return body as T;
}
