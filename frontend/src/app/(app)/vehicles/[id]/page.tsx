"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";
import {
  ACCEPT,
  MAX_FILES_PER_DOCUMENT,
  MAX_FILE_MB,
  fileUrl,
  formatBytes,
  type VehicleDocument,
} from "@/lib/documents";
import { vehicleTitle, type Vehicle } from "@/lib/vehicles";

export default function VehiclePage() {
  const { id } = useParams<{ id: string }>();
  const [vehicle, setVehicle] = useState<Vehicle>();
  const [documents, setDocuments] = useState<VehicleDocument[]>();
  const [error, setError] = useState<string>();

  const loadDocuments = useCallback(() => {
    api<VehicleDocument[]>(`/vehicles/${id}/documents`)
      .then(setDocuments)
      .catch((err) => setError(err instanceof Error ? err.message : "Couldn't load documents"));
  }, [id]);

  useEffect(() => {
    api<Vehicle>(`/vehicles/${id}`)
      .then(setVehicle)
      .catch((err) => setError(err instanceof Error ? err.message : "Couldn't load vehicle"));
    loadDocuments();
  }, [id, loadDocuments]);

  if (error) {
    return (
      <Card>
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
        <Link href="/" className="mt-3 inline-block text-sm text-muted hover:text-text">
          ← Back to vehicles
        </Link>
      </Card>
    );
  }
  if (!vehicle) return <p className="text-sm text-muted">Loading…</p>;

  return (
    <div className="flex flex-col gap-6">
      <Link href="/" className="text-sm text-muted hover:text-text">
        ← Vehicles
      </Link>

      <Card>
        <h1 className="text-xl font-semibold">
          {vehicle.nickname ?? vehicleTitle(vehicle)}
          {!vehicle.nickname && vehicle.trim ? <span className="text-muted"> {vehicle.trim}</span> : null}
        </h1>
        <dl className="mt-3 grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
          {vehicle.nickname && <Detail label="Vehicle" value={`${vehicleTitle(vehicle)} ${vehicle.trim ?? ""}`} />}
          <Detail label="Engine" value={vehicle.engine} />
          <Detail label="Transmission" value={vehicle.transmission} />
          <Detail label="VIN" value={vehicle.vin} mono />
        </dl>
      </Card>

      <UploadCard vehicleId={vehicle.id} onUploaded={loadDocuments} />

      <Card>
        <h2 className="text-lg font-semibold">Documents</h2>
        {documents === undefined ? (
          <p className="mt-3 text-sm text-muted">Loading…</p>
        ) : documents.length === 0 ? (
          <p className="mt-3 text-sm text-muted">
            No documents yet. Upload an invoice or inspection report from your last service visit.
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-border">
            {documents.map((doc) => (
              <DocumentRow key={doc.id} document={doc} />
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function Detail({ label, value, mono = false }: { label: string; value: string | null; mono?: boolean }) {
  return (
    <div className="flex gap-2">
      <dt className="text-muted">{label}:</dt>
      <dd className={mono ? "font-mono tracking-wider" : ""}>{value || "—"}</dd>
    </div>
  );
}

function DocumentRow({ document }: { document: VehicleDocument }) {
  const uploaded = new Date(document.created_at).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
  return (
    <li className="flex flex-col gap-2 py-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="font-medium">{document.note ?? `Document uploaded ${uploaded}`}</p>
        <span className="rounded-full border border-border px-2.5 py-0.5 text-xs text-muted">
          {document.extraction_status === "pending" ? "Not yet read" : document.extraction_status}
        </span>
      </div>
      {document.note && <p className="text-xs text-muted">Uploaded {uploaded}</p>}
      <ul className="flex flex-col gap-1 text-sm">
        {document.files.map((file) => (
          <li key={file.id} className="flex flex-wrap items-center gap-x-2">
            <a
              href={fileUrl(document.id, file.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              {file.original_filename}
            </a>
            <span className="text-muted">
              {formatBytes(file.size_bytes)}
              {file.converted_from === "image/heic" ? " · converted from HEIC" : ""}
            </span>
          </li>
        ))}
      </ul>
    </li>
  );
}

function UploadCard({ vehicleId, onUploaded }: { vehicleId: number; onUploaded: () => void }) {
  const formRef = useRef<HTMLFormElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string>();
  const [uploading, setUploading] = useState(false);

  function validate(chosen: File[]): string | undefined {
    if (chosen.length > MAX_FILES_PER_DOCUMENT) return `Choose at most ${MAX_FILES_PER_DOCUMENT} files.`;
    const big = chosen.find((f) => f.size > MAX_FILE_MB * 1024 * 1024);
    if (big) return `“${big.name}” is larger than ${MAX_FILE_MB} MB.`;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const problem = files.length ? validate(files) : "Choose at least one file.";
    if (problem) return setError(problem);

    const body = new FormData();
    files.forEach((f) => body.append("files", f));
    const note = String(new FormData(event.currentTarget).get("note") ?? "").trim();
    if (note) body.append("note", note);

    setError(undefined);
    setUploading(true);
    try {
      await api(`/vehicles/${vehicleId}/documents`, { method: "POST", body });
      formRef.current?.reset();
      setFiles([]);
      onUploaded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <Card>
      <form ref={formRef} onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
        <div>
          <h2 className="text-lg font-semibold">Upload a service document</h2>
          <p className="mt-1 text-sm text-muted">
            Invoice, multi-point inspection, battery test… PDF or photos (JPEG, PNG, HEIC), up to {MAX_FILE_MB} MB
            each. For a multi-page paper, select all its pages together.
          </p>
        </div>

        <label className="flex cursor-pointer flex-col items-center justify-center gap-1 rounded-control border border-dashed border-border bg-surface-raised px-4 py-6 text-center hover:border-accent">
          <span className="text-sm font-medium">{files.length ? "Change files" : "Choose files or take photos"}</span>
          <span className="text-xs text-muted">Tap to browse</span>
          <input
            type="file"
            name="files"
            multiple
            accept={ACCEPT}
            className="sr-only"
            onChange={(e) => {
              const chosen = Array.from(e.target.files ?? []);
              setFiles(chosen);
              setError(validate(chosen));
            }}
          />
        </label>

        {files.length > 0 && (
          <ol className="flex flex-col gap-1 text-sm">
            {files.map((f, i) => (
              <li key={`${f.name}-${i}`} className="flex justify-between gap-3">
                <span className="truncate">
                  {i + 1}. {f.name}
                </span>
                <span className="shrink-0 text-muted">{formatBytes(f.size)}</span>
              </li>
            ))}
          </ol>
        )}

        <Input label="Note (optional)" name="note" maxLength={500} placeholder="e.g. 60k service at Honda dealer" />

        {error && (
          <p role="alert" className="text-sm text-danger">
            {error}
          </p>
        )}
        <Button type="submit" loading={uploading} disabled={!files.length}>
          Upload {files.length > 1 ? `${files.length} files as one document` : "document"}
        </Button>
      </form>
    </Card>
  );
}
