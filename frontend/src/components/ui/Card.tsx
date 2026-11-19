import type { HTMLAttributes } from "react";

/** Rounded surface used for every content block. */
export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-card border border-border bg-surface p-5 sm:p-6 ${className}`}
      {...props}
    />
  );
}
