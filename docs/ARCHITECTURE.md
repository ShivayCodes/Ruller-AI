# Ruller AI architecture

## Current implementation

Ruller AI is an offline-first Python assistant baseline, not a trained large language model.

- **CLI** — interactive terminal interface and command parsing.
- **Engine** — routes commands and orchestrates memory and knowledge retrieval.
- **Memory store** — bounded conversation history stored as local JSON.
- **Knowledge base** — text ingestion and explainable lexical-overlap retrieval.
- **Arithmetic evaluator** — Python AST allowlist; never calls `eval` or `exec`.
- **Storage** — atomic JSON writes and readable local files.

## Data and privacy

By default, data is written to `~/.ruller_ai/`. Use `--data-dir` to choose another directory. Memory and knowledge are local and are not uploaded by this application. Do not ingest secrets or files you do not have permission to use. Back up or delete this directory according to your needs.

## Retrieval behavior

The current knowledge search tokenizes text and ranks it by the proportion of query tokens shared with each stored passage. This is deliberately small and transparent, but it is not semantic search, does not understand meaning reliably, and can return irrelevant matches. Always inspect sources and verify important claims.

## Planned extension points

1. Add a typed model-provider interface (local model first, optional provider adapters).
2. Add model timeouts, output-size limits, and explicit user consent for network calls.
3. Add embedding-based retrieval as an optional dependency.
4. Add evaluations for answer relevance, factuality, latency, and resource use.
5. Add permissioned tools with explicit allowlists and audit logs.

These are future work, not features currently implemented. Ruller AI does not claim consciousness, unlimited intelligence, autonomous self-improvement, or AGI.
