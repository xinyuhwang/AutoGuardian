import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-accent text-on-accent hover:bg-accent-hover",
  secondary: "border border-border bg-surface-raised text-text hover:border-muted",
  ghost: "text-muted hover:text-text",
};

/**
 * The one place that defines how buttons look. Also used for links that should look like
 * buttons: <Link className={buttonClasses("primary")}>.
 */
export function buttonClasses(variant: Variant = "primary", fullWidth = false): string {
  return [
    "inline-flex h-11 items-center justify-center gap-2 rounded-control px-5 text-sm font-semibold",
    "transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
    "disabled:cursor-not-allowed disabled:opacity-60",
    VARIANTS[variant],
    fullWidth ? "w-full" : "",
  ].join(" ");
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  loading?: boolean;
  fullWidth?: boolean;
};

export function Button({
  variant = "primary",
  loading = false,
  fullWidth = false,
  disabled,
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={`${buttonClasses(variant, fullWidth)} ${className}`}
      {...props}
    >
      {loading && (
        <span
          aria-hidden
          className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      )}
      {children}
    </button>
  );
}
