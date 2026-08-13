# Spark Master Index

## Target Executor
GPT-5.3-Codex-Spark

## Execution Rule
Load shared task/context files and only the active chunk. Exactly one chunk may be `RUNNING`. A successful non-final chunk stops at its user-approval gate before the next chunk is read or executed.

## Chunk Status
- CHUNK-001: READY — {bounded outcome}
- CHUNK-002: READY — {bounded outcome}

## Dependency Map
- CHUNK-002 requires: {recorded output from CHUNK-001}

## High-Model Gates
- {gate or NONE}
