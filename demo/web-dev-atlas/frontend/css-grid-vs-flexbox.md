---
type: reference
title: "CSS Grid vs Flexbox"
description: "Choosing 1D Flexbox alignment vs 2D CSS Grid layouts for responsive web interfaces."
tags: [frontend, css, layout]
resource: https://web.dev/learn/css/grid
---

# CSS Grid vs Flexbox

Both Flexbox and CSS Grid are modern layout engines, solving different dimensional problems.

## When to Use Which
- **Flexbox (1D):** Navbars, button groups, and single-axis wrapping or alignment.
- **CSS Grid (2D):** Full-page shells, dashboards, and asymmetric card grids (`grid-template-columns: repeat(auto-fit, minmax(250px, 1fr))`).
- Reserve explicit dimensions on media containers to avoid layout shifts in the [rendering pipeline](dom-and-reflow.md).
