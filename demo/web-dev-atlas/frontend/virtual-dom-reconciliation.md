---
type: technical-note
title: "Virtual DOM and Diffing Reconciliation"
description: "How declarative UI frameworks batch state updates and reconcile component trees."
tags: [frontend, react, architecture]
resource: https://react.dev/learn/preserving-and-resetting-state
---

# Virtual DOM and Diffing Reconciliation

Declarative UI libraries represent UI as a lightweight tree of descriptors and compute minimal DOM mutations on state change.

## Key Rules
- **Keys Matter:** Stable `key` props let list reconciliation match moved/reordered items in $O(n)$.
- **Avoid Unnecessary Subtree Renders:** Memoize expensive leaves and keep state local.
- Connects to server-rendered markup during [SSR hydration](hydration-and-ssr.md).
