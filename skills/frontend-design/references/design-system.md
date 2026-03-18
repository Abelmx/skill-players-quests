# Design System

## Typography

### FORBIDDEN fonts

- Inter
- Arial
- Roboto
- Helvetica
- system-ui
- sans-serif (as sole font)

### REQUIRED

- Import at least one Google Font
- Suggested: Space Mono, Playfair Display, DM Serif Display, Instrument Serif, Syne, Unbounded

## Colors

### REQUIRED

- Use CSS custom properties (variables) for colors

## Motion

### REQUIRED

- Include CSS animations or transitions

## Layout

### REQUIRED

- Non-centered-card layout
- Use asymmetric, grid-breaking, or overlap layouts

### FORBIDDEN

- Purple gradients
- Generic card-stack layouts

## Accessibility (WCAG 2.1 AA)

- All inputs must have labels or `aria-label`
- Forms need appropriate `role` attributes
- Buttons need explicit text (not icon-only without accessible name)
- Interactive elements need focus styles
- Use `aria-required` on required fields
- Color contrast must meet 4.5:1 ratio
