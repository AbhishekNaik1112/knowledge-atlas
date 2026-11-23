---
type: technical-note
title: "Modern Image Formats: AVIF, WebP, and Responsive Srcset"
description: "Delivering appropriately sized AVIF/WebP images to cut page weight without losing quality."
tags: [performance, frontend, images]
resource: https://web.dev/articles/choose-the-right-image-format
---

# Modern Image Formats: AVIF, WebP, and Responsive Srcset

Images account for over half of typical web page bytes.

## Checklist
- **Formats:** Serve **AVIF** (best compression) with **WebP** fallback via `<picture>` or [content negotiation](../http/content-negotiation.md).
- **Responsive Sizes:** Use `srcset` and `sizes` so mobile devices don't download desktop 4K assets.
- **Explicit `width`/`height`:** Prevents layout shift ([CLS](core-web-vitals.md)).
