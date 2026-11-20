"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";

/** Layout for every signed-in page: header + redirect to /login when logged out. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user === null) router.replace("/login");
  }, [user, router]);

  if (!user) {
    return <p className="p-6 text-center text-sm text-muted">Loading…</p>;
  }

  return (
    <div className="mx-auto flex min-h-dvh w-full max-w-3xl flex-col gap-6 px-4 py-6 sm:py-10">
      <header className="flex items-center justify-between gap-4">
        <Link href="/">
          <Logo className="text-lg" />
        </Link>
        <div className="flex items-center gap-1">
          <span className="hidden text-sm text-muted sm:inline">{user.email}</span>
          <Button variant="ghost" onClick={() => logout()}>
            Log out
          </Button>
        </div>
      </header>
      {children}
    </div>
  );
}
