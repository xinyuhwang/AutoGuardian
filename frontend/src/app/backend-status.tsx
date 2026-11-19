"use client";

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";

type Status = "checking" | "ok" | "unreachable";

export function BackendStatus() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((body) => setStatus(body.status === "ok" ? "ok" : "unreachable"))
      .catch(() => setStatus("unreachable"));
  }, []);

  const label = {
    checking: "Checking backend…",
    ok: "Backend connected",
    unreachable: `Backend unreachable at ${API_URL}`,
  }[status];

  return <p data-status={status}>{label}</p>;
}
