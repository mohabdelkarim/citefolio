# Citefolio visual system

World: editorial research desk — ink on cool paper, precise tools.

## Tokens

- Bone paper: `#E8E4DC`
- Ink: `#12141A`
- Muted steel: `#3D4A5C`
- Accent ink red: `#C45C4A` (CTA / active only)

## Type

- Display: Fraunces
- UI / body: IBM Plex Sans
- Labels: IBM Plex Mono

## Motion

Upload ready pulse, stream caret blink, source chip enter. Nothing else.

## Chat surface

Operate mode: conversation wells on bone (user ink-tint, assistant paper tint), sticky composer, thin ink scrollbar on `.chat__log`, source chips under assistant turns. Markdown lists/bold/paragraphs only — no purple SaaS chrome.

## Layout

Mobile-first stacked (brand → chat). Two-zone from 1024px. Touch targets ≥44px. Chat pane uses `dvh` + flex so composer stays usable; iOS safe-area insets honored.
