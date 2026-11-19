# AutoGuardian frontend

Next.js (App Router) + TypeScript web app. UI only. All data and logic come from the FastAPI backend.

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

Note: this uses Next.js 16. See `AGENTS.md` and `node_modules/next/dist/docs/` for version-specific APIs.
