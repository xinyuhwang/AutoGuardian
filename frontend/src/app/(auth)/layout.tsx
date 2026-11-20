"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/Logo";
import { useAuth } from "@/lib/auth";

/** Shared layout for /login and /signup. Signed-in users are sent to the home page. */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) router.replace("/");
  }, [user, router]);

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col justify-center gap-8 px-4 py-12">
      <div className="flex flex-col items-center gap-2 text-center">
        <Logo className="text-2xl" />
        <p className="text-sm text-muted">Your personal vehicle health assistant</p>
      </div>
      {children}
    </main>
  );
}
