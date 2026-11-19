"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/lib/auth";

const MIN_PASSWORD = 8; // matches the backend rule

type FieldErrors = { email?: string; password?: string; confirm?: string; form?: string };

export default function SignupPage() {
  const { signup } = useAuth();
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email")).trim();
    const password = String(form.get("password"));
    const confirm = String(form.get("confirm"));

    const next: FieldErrors = {};
    if (!email.includes("@")) next.email = "Enter a valid email address";
    if (password.length < MIN_PASSWORD) next.password = `Use at least ${MIN_PASSWORD} characters`;
    if (confirm !== password) next.confirm = "Passwords don't match";
    setErrors(next);
    if (Object.keys(next).length) return;

    setSubmitting(true);
    try {
      await signup(email, password);
      // AuthLayout redirects to "/" once the user is set.
    } catch (err) {
      setErrors({ form: err instanceof Error ? err.message : "Sign-up failed" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <h1 className="text-xl font-semibold">Create your account</h1>
        <Input label="Email" name="email" type="email" autoComplete="email" error={errors.email} required />
        <Input
          label="Password"
          name="password"
          type="password"
          autoComplete="new-password"
          hint={`At least ${MIN_PASSWORD} characters`}
          error={errors.password}
          required
        />
        {/* Confirm field matters because there's no password reset yet. */}
        <Input
          label="Confirm password"
          name="confirm"
          type="password"
          autoComplete="new-password"
          error={errors.confirm}
          required
        />
        {errors.form && (
          <p role="alert" className="text-sm text-danger">
            {errors.form}
          </p>
        )}
        <Button type="submit" loading={submitting} fullWidth>
          Create account
        </Button>
        <p className="text-center text-sm text-muted">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-accent hover:underline">
            Log in
          </Link>
        </p>
      </form>
    </Card>
  );
}
