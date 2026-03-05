# Architecture

## Components

- gateway
- runtime
- worker
- postgres
- redis

## Data flow

Lovable -> gateway -> worker -> runtime -> postgres

## State transitions

Runs can be queued, running, waiting_approval, completed, or failed.
