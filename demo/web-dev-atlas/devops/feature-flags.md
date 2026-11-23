---
type: pattern
title: "Feature Flags and Progressive Delivery"
description: "Decoupling code deployment from feature release using runtime configuration."
tags: [devops, architecture, deployment]
resource: https://martinfowler.com/articles/feature-toggles.html
---

# Feature Flags and Progressive Delivery

Feature flags let teams merge and deploy code safely behind a runtime toggle, enabling instant kill-switches without redeploying.

## Hygiene
- Keep flag evaluation fast (in-memory rules) and clean up expired release flags regularly.
- Pairs with [canary rollouts](blue-green-deployments.md) and A/B experiments.
