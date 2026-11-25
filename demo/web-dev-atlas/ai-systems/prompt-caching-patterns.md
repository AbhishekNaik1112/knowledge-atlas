---
type: technical-note
title: "Prompt Caching Patterns for Long Context"
description: "Ordering stable system instructions and schemas before dynamic queries to reduce LLM latency and token cost."
tags: [ai-systems, caching, llm, performance]
---

# Prompt Caching Patterns for Long Context

Prompt caching reuses KV-cache prefixes across requests when the leading tokens remain byte-for-byte identical.

## Practical Rules
- **Prefix Stability:** Keep system prompts, tool schemas, and reference specs at the very top of the prompt.
- **Append-Only Context:** Place changing user queries and retrieved notes from [compounding LLM wikis](rag-vs-llm-wiki.md) at the end.
- **Batching:** Reuse identical tool definitions across turns to avoid cache invalidation.
