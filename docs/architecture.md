# Architecture

## Monorepo Layout

Recommended project layout:

```text
apps/
  api/
  web/
packages/
  shared/
  ui/
docs/
```

## Rules

- Put deployable applications under `apps/`.
- Put reusable cross-app code under `packages/`.
- Keep frontend-specific rules in `FRONTEND_REFERENCE.md`.
- Keep API contracts and platform decisions in `docs/`.
- Do not place permission or role enforcement in shared client packages.

## Migration Status

- API app: moved under `apps/api/src/`.
- Web app: not started.
- Shared package: not started.
