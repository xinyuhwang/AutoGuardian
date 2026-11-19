"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Vehicle = { id: number; year: number; make: string; model: string; trim: string | null; nickname: string | null };

export default function HomePage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [vehicles, setVehicles] = useState<Vehicle[]>();
  const [error, setError] = useState<string>();

  useEffect(() => {
    if (user === null) router.replace("/login");
    if (user) {
      api<Vehicle[]>("/vehicles")
        .then(setVehicles)
        .catch((err) => setError(err instanceof Error ? err.message : "Couldn't load vehicles"));
    }
  }, [user, router]);

  if (!user) {
    return <p className="p-6 text-center text-sm text-muted">Loading…</p>;
  }

  return (
    <div className="mx-auto flex min-h-dvh w-full max-w-3xl flex-col gap-6 px-4 py-6 sm:py-10">
      <header className="flex items-center justify-between gap-4">
        <Logo className="text-lg" />
        <div className="flex items-center gap-1">
          <span className="hidden text-sm text-muted sm:inline">{user.email}</span>
          <Button variant="ghost" onClick={() => logout()}>
            Log out
          </Button>
        </div>
      </header>

      <Card>
        <h1 className="text-lg font-semibold">Your vehicles</h1>
        {error ? (
          <p role="alert" className="mt-3 text-sm text-danger">
            {error}
          </p>
        ) : vehicles === undefined ? (
          <p className="mt-3 text-sm text-muted">Loading…</p>
        ) : vehicles.length === 0 ? (
          <p className="mt-3 text-sm text-muted">
            No vehicles yet. Adding a car by VIN is coming in the next step.
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-border">
            {vehicles.map((v) => (
              <li key={v.id} className="py-3">
                <p className="font-medium">{v.nickname ?? `${v.year} ${v.make} ${v.model}`}</p>
                {v.nickname || v.trim ? (
                  <p className="text-sm text-muted">
                    {[v.nickname && `${v.year} ${v.make} ${v.model}`, v.trim].filter(Boolean).join(" · ")}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
