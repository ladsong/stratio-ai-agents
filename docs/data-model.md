# Data model (draft)

## Core

- threads
- events
- runs
- run_approvals
- artifacts
- tool_calls

## Knowledge

- knowledge_documents
- knowledge_chunks (vector column for pgvector)

## Registry

- graph_registry
- tool_registry

## Config & Policy

- integration_credentials (encrypted API tokens and secrets)
- tool_policies (allowlist-based tool access control)
