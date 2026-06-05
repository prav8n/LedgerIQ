# LedgerIQ — Frontend

React 19 + TypeScript (strict) + Vite + MUI + React Query + Zustand.

## Prerequisites
- Node.js 20.19+ (or 22.12+) and npm

## Setup
```bash
cd frontend
cp .env.example .env          # points at http://localhost:8000/api/v1 by default
npm install
npm run dev                   # http://localhost:5173
```

Make sure the backend (Phase 1–4) is running on port 8000 with CORS allowing
`http://localhost:5173`.

## Scripts
- `npm run dev` — start the Vite dev server
- `npm run typecheck` — strict TypeScript check (`tsc --noEmit`)
- `npm run build` — typecheck + production build
- `npm run preview` — preview the production build

## Structure
```
src/
  theme/        MUI light/dark theme + provider
  store/        Zustand stores (auth, theme, toasts)
  services/     Axios instance (+ token refresh) and API services
  routes/       AppRouter, PrivateRoute, path constants
  layouts/      MainLayout (responsive sidebar + bottom nav) and parts
  components/    ErrorBoundary, LoadingSkeleton, ToastViewport, EmptyState…
  pages/        Login, Register, and one page per module
  hooks/        useToast
  config/       React Query client
  types/        API/domain types
```

## What works in this phase
- Login & Register against the backend auth API (tokens persisted, auto-login).
- Protected routing — unauthenticated users are redirected to `/login`.
- Axios interceptors with single-flight access-token refresh on 401.
- Light/Dark theme toggle (persisted), responsive shell, toasts, error boundary.
- Every module has a placeholder page wired into the nav (data arrives later).
