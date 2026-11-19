export function Logo({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 font-semibold tracking-tight ${className}`}>
      <span aria-hidden className="size-2.5 rounded-full bg-accent shadow-[0_0_12px] shadow-accent" />
      AutoGuardian
    </span>
  );
}
