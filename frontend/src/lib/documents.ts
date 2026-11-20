import { API_URL } from "@/lib/api";

export type DocumentFile = {
  id: number;
  position: number;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  converted_from: string | null;
};

export type VehicleDocument = {
  id: number;
  vehicle_id: number;
  kind: string | null;
  note: string | null;
  extraction_status: string;
  created_at: string;
  files: DocumentFile[];
};

// Keep in sync with backend/app/config.py.
export const MAX_FILE_MB = 20;
export const MAX_FILES_PER_DOCUMENT = 20;
export const ACCEPT = "application/pdf,image/jpeg,image/png,image/heic,image/heif,.pdf,.jpg,.jpeg,.png,.heic,.heif";

export function fileUrl(documentId: number, fileId: number): string {
  return `${API_URL}/documents/${documentId}/files/${fileId}`;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
