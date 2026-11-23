---
type: reference
title: "Web Accessibility (WCAG) and ARIA"
description: "Building keyboard-navigable, screen-reader-friendly UIs with semantic HTML and ARIA."
tags: [frontend, accessibility, html]
resource: https://www.w3.org/WAI/ARIA/apg/
---

# Web Accessibility (WCAG) and ARIA

Accessible web apps work for everyone, including keyboard-only and screen-reader users.

## Core Principles
- **Semantic HTML First:** Prefer `<button>`, `<nav>`, `<main>`, and `<label>` before reaching for `role=` attributes.
- **Focus Management:** Maintain visible `:focus-visible` rings and trap focus inside open modals.
- **Contrast:** Meet WCAG AA 4.5:1 text contrast ratios.
