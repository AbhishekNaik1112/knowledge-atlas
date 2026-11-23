---
type: technical-note
title: "End-to-End Browser Testing"
description: "Verifying critical user journeys across UI, network, and database with headless browsers."
tags: [testing, frontend, e2e]
resource: https://playwright.dev/docs/intro
---

# End-to-End Browser Testing

End-to-end (E2E) tests drive a real browser against your running app to catch wiring issues across HTML, JavaScript, and backend APIs.

## Best Practices
- Keep E2E suites focused on critical user flows (auth, search, checkout) while covering edge cases in [unit and integration tests](unit-vs-integration-testing.md).
- Use role/text locators aligned with [web accessibility](../frontend/accessibility-aria.md) rather than brittle CSS selectors.
