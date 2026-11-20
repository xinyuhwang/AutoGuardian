"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";
import type { Vehicle, VehicleInput, VinDecode } from "@/lib/vehicles";

/**
 * Add a vehicle in two parts:
 *  1. Enter the VIN → NHTSA proposes year/make/model/trim/engine/transmission.
 *  2. Review and correct every field, then save. Nothing is stored until "Save vehicle".
 * Users without a VIN can skip straight to part 2.
 */
export default function NewVehiclePage() {
  const [decoded, setDecoded] = useState<VinDecode | null>(null);
  const [stage, setStage] = useState<"vin" | "details">("vin");

  return (
    <div className="flex flex-col gap-4">
      <Link href="/" className="text-sm text-muted hover:text-text">
        ← Back
      </Link>
      {stage === "vin" ? (
        <VinStep
          onDecoded={(d) => {
            setDecoded(d);
            setStage("details");
          }}
          onManual={() => {
            setDecoded(null);
            setStage("details");
          }}
        />
      ) : (
        <DetailsStep decoded={decoded} onBack={() => setStage("vin")} />
      )}
    </div>
  );
}

function VinStep({ onDecoded, onManual }: { onDecoded: (d: VinDecode) => void; onManual: () => void }) {
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const vin = String(new FormData(event.currentTarget).get("vin")).trim();
    setError(undefined);
    setLoading(true);
    try {
      onDecoded(await api<VinDecode>(`/vehicles/decode-vin?vin=${encodeURIComponent(vin)}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "VIN lookup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <div>
          <h1 className="text-xl font-semibold">Add a vehicle</h1>
          <p className="mt-1 text-sm text-muted">
            We&apos;ll look up your car&apos;s details from its VIN using NHTSA&apos;s official database.
          </p>
        </div>
        <Input
          label="VIN"
          name="vin"
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          maxLength={40}
          placeholder="17 characters"
          className="font-mono uppercase tracking-wider"
          hint="Find it on the driver-side dashboard (through the windshield), your registration, or insurance card."
          error={error}
        />
        <Button type="submit" loading={loading} fullWidth>
          Look up VIN
        </Button>
        <button type="button" onClick={onManual} className="text-sm text-muted hover:text-text">
          Don&apos;t have your VIN? Enter details manually
        </button>
      </form>
    </Card>
  );
}

function DetailsStep({ decoded, onBack }: { decoded: VinDecode | null; onBack: () => void }) {
  const router = useRouter();
  const [error, setError] = useState<string>();
  const [saving, setSaving] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const f = new FormData(event.currentTarget);
    const text = (name: string) => String(f.get(name) ?? "").trim() || null;
    const year = Number(text("year"));
    const make = text("make");
    const model = text("model");
    if (!year || !make || !model) {
      setError("Year, make and model are required.");
      return;
    }
    const mileage = text("purchase_mileage");
    const body: VehicleInput = {
      vin: decoded?.vin ?? null,
      year,
      make,
      model,
      trim: text("trim"),
      engine: text("engine"),
      transmission: text("transmission"),
      nickname: text("nickname"),
      purchase_date: text("purchase_date"),
      purchase_mileage: mileage ? Number(mileage.replace(/[,\s]/g, "")) : null,
      home_zip: text("home_zip"),
    };
    setError(undefined);
    setSaving(true);
    try {
      const saved = await api<Vehicle>("/vehicles", { method: "POST", body: JSON.stringify(body) });
      router.push(`/vehicles/${saved.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't save the vehicle");
      setSaving(false);
    }
  }

  return (
    <Card>
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <div>
          <h1 className="text-xl font-semibold">Confirm your vehicle</h1>
          <p className="mt-1 text-sm text-muted">
            {decoded
              ? `Details below come from ${decoded.source}. Check each one and correct anything that's wrong.`
              : "Enter what you know; you can add the VIN later."}
          </p>
        </div>

        {decoded && (
          <div className="rounded-control border border-border bg-surface-raised p-3 text-sm">
            <p className="font-mono tracking-wider">{decoded.vin}</p>
            {[decoded.body_class, decoded.drive_type, decoded.fuel_type].some(Boolean) && (
              <p className="mt-1 text-muted">
                {[decoded.body_class, decoded.drive_type, decoded.fuel_type].filter(Boolean).join(" · ")}
              </p>
            )}
          </div>
        )}

        {decoded?.warnings.map((w) => (
          <p key={w} role="alert" className="rounded-control border border-warn/40 bg-warn/10 p-3 text-sm text-warn">
            {w}
          </p>
        ))}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Input label="Year" name="year" inputMode="numeric" defaultValue={decoded?.year ?? ""} required />
          <Input label="Make" name="make" defaultValue={decoded?.make ?? ""} required />
          <Input label="Model" name="model" defaultValue={decoded?.model ?? ""} required />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input label="Trim" name="trim" defaultValue={decoded?.trim ?? ""} placeholder="e.g. EX-L" />
          <Input label="Transmission" name="transmission" defaultValue={decoded?.transmission ?? ""} />
        </div>
        <Input label="Engine" name="engine" defaultValue={decoded?.engine ?? ""} placeholder="e.g. 1.5L 4-cyl turbo" />

        <hr className="border-border" />
        <p className="text-sm font-medium">Optional</p>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input label="Nickname" name="nickname" placeholder="e.g. My Accord" />
          <Input
            label="Home ZIP code"
            name="home_zip"
            inputMode="numeric"
            hint="Used for climate-aware reminders (heat and cold affect batteries)."
          />
          <Input label="Purchase date" name="purchase_date" type="date" />
          <Input
            label="Mileage when purchased"
            name="purchase_mileage"
            inputMode="numeric"
            placeholder="e.g. 12,500"
          />
        </div>

        {error && (
          <p role="alert" className="text-sm text-danger">
            {error}
          </p>
        )}
        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button type="button" variant="secondary" onClick={onBack}>
            {decoded ? "Use a different VIN" : "Back"}
          </Button>
          <Button type="submit" loading={saving}>
            Save vehicle
          </Button>
        </div>
      </form>
    </Card>
  );
}
