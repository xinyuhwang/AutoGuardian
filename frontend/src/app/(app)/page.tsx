"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { buttonClasses } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { vehicleTitle, type Vehicle } from "@/lib/vehicles";

export default function HomePage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>();
  const [error, setError] = useState<string>();

  useEffect(() => {
    api<Vehicle[]>("/vehicles")
      .then(setVehicles)
      .catch((err) => setError(err instanceof Error ? err.message : "Couldn't load vehicles"));
  }, []);

  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-lg font-semibold">Your vehicles</h1>
        <Link href="/vehicles/new" className={buttonClasses("primary")}>
          Add vehicle
        </Link>
      </div>
      {error ? (
        <p role="alert" className="mt-3 text-sm text-danger">
          {error}
        </p>
      ) : vehicles === undefined ? (
        <p className="mt-3 text-sm text-muted">Loading…</p>
      ) : vehicles.length === 0 ? (
        <p className="mt-3 text-sm text-muted">No vehicles yet. Add your car to get started.</p>
      ) : (
        <ul className="mt-3 divide-y divide-border">
          {vehicles.map((v) => (
            <li key={v.id}>
              <Link href={`/vehicles/${v.id}`} className="-mx-2 block rounded-control px-2 py-3 hover:bg-surface-raised">
                <p className="font-medium">
                  {v.nickname ?? vehicleTitle(v)}
                  {!v.nickname && v.trim ? <span className="text-muted"> {v.trim}</span> : null}
                </p>
                <p className="text-sm text-muted">
                  {[v.nickname && `${vehicleTitle(v)}${v.trim ? ` ${v.trim}` : ""}`, v.engine, v.transmission]
                    .filter(Boolean)
                    .join(" · ") || "Details not set"}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
