# React + Vite

This template provides a minimal setup to get React working in Vite with some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on build performance. To add it, see the [React Compiler installation documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

For type-aware lint rules, use TypeScript and check the [Vite React TypeScript template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts).

## Frontend-only demo on Vercel

This folder can be deployed as a static Vite site for a project demonstration.

- Root directory: `frontend`
- Framework preset: Vite
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_DEMO_MODE=true`

The demo uses synthetic sample values held only in browser memory. It does not need FastAPI, Render, Turso, a database, authentication credentials, or backend environment variables. A browser refresh restores the original sample dataset. `vercel.json` routes direct page visits and refreshes back to the Vite single-page app.

With `VITE_DEMO_MODE` unset or set to `false`, the existing local full-stack frontend continues to use the API client and Vite development proxy.
