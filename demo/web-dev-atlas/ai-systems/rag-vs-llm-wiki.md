---
type: architecture-guide
title: "RAG vs. Compounding LLM Wiki"
description: "Why persistent, cross-linked Markdown wikis outperform stateless one-shot RAG for personal knowledge bases."
tags: [ai-systems, second-brain, llm-wiki, knowledge-graph]
---

# RAG vs. Compounding LLM Wiki

Stateless RAG re-retrieves raw chunks on every question without saving synthesis. An **LLM Wiki** compiles sources into atomic, cross-linked concept pages that grow denser over time.

## Key Differences
- **Stateless RAG:** Upload source, retrieve top-k chunks, discard synthesis after the chat closes.
- **Compounding Wiki:** Extract concepts, resolve cross-links, and track contradictions in a persistent graph.
- **Storage & Embeddings:** Pair compact [Matryoshka vector embeddings](vector-embeddings-matryoshka.md) with structured edges exposed over [Streamable HTTP MCP](mcp-streamable-http.md).
