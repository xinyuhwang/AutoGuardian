# AutoGuardian frontend

Next.js (App Router) + TypeScript + Tailwind CSS v4. UI only. All data and logic come from the
FastAPI backend.

Requires **Node 20.19+ or 22.12+** (Tailwind v4 needs it; Node 21 fails the build).

```bash
pnpm install
pnpm dev        # http://localhost:3000  (use --port 3010 etc. if 3000 is taken)
pnpm lint
pnpm build
```

Environment variables (put them in `.env.local`, which git ignores):

| Name | Default | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of the backend |

## Styling

- **Theme tokens** live in `src/app/globals.css` (`@theme`): colors, radii, fonts. Change a value
  there to restyle every screen.
- Use the role names (`bg-surface`, `text-muted`, `text-accent`, `rounded-card`, ...), never raw
  Tailwind colors like `bg-zinc-900`, so the theme stays changeable in one place.
- Shared components in `src/components/ui/` (`Button`, `Input`, `Card`) define how each kind of
  element looks; pages compose them.

## Structure

```text
src/app/(auth)/   login + signup pages; layout sends signed-in users home
src/app/(app)/    signed-in pages; layout has the header and sends logged-out users to /login
  page.tsx            home (vehicle list)
  vehicles/new/       add vehicle: VIN lookup → confirm details → save
  vehicles/[id]/      vehicle details, document upload, document list
src/components/   Logo + ui/ building blocks
src/lib/api.ts    fetch wrapper (sends the session cookie, readable errors)
src/lib/auth.tsx  AuthProvider + useAuth() (current user, login, signup, logout)
src/lib/vehicles.ts  Vehicle / VinDecode types
src/lib/documents.ts Document types, upload limits, file URLs
```

Note: this uses Next.js 16. See `AGENTS.md` and `node_modules/next/dist/docs/` for version-specific APIs.
