import { useId, type InputHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string;
};

/** Labeled text input with optional hint and error message. */
export function Input({ label, hint, error, id, className = "", ...props }: InputProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-medium text-text">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={[
          "h-11 rounded-control border bg-surface-raised px-3.5 text-base text-text placeholder:text-muted",
          "outline-none transition-colors focus:border-accent",
          error ? "border-danger" : "border-border",
          className,
        ].join(" ")}
        {...props}
      />
      {error ? (
        <p id={`${inputId}-error`} className="text-sm text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={`${inputId}-hint`} className="text-sm text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
