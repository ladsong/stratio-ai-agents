# OpenAPI Draft (MVP)

## Health

- GET /health
- GET /ready

## Threads

- POST /api/v1/threads
- GET /api/v1/threads/{id}

## Events

- POST /api/v1/threads/{id}/events
- GET /api/v1/threads/{id}/events

## Runs

- POST /api/v1/runs
- GET /api/v1/runs/{id}
- GET /api/v1/runs/{id}/state

## Approval

- POST /api/v1/runs/{id}/approve
- POST /api/v1/runs/{id}/reject
- POST /api/v1/runs/{id}/resume

## Artifacts

- GET /api/v1/artifacts/{id}

## Registry

- GET /api/v1/tools
- GET /api/v1/graphs
