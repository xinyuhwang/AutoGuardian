// Base URL of the FastAPI backend. Override with NEXT_PUBLIC_API_URL in .env.local.
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
