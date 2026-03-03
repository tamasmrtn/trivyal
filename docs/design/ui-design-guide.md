# Trivyal UI Design Guide

Trivyal is a self-hosted, developer-facing security tool. The UI should feel like an instrument panel: precise, information-dense without being cluttered. Every design decision should communicate trust and quiet competence — nothing decorative unless it carries meaning.

The app opens in **dark mode by default**. Light mode is available via the theme toggle. Both modes share the same layout, typography, component structure, and brand identity — only the surface colours change.

---

## Colour Palette

### Shared Brand Tokens

These named roles exist in both modes. The values differ; the semantics do not.

| Role | Dark value | Light value | Usage |
|------|-----------|-------------|-------|
| Background | `#0f1117` | `#ffffff` | App root, page canvas |
| Surface | `#1a1f2e` | `#e8edf5` | Cards, panels, dialogs, sidebar |
| Accent surface | `#1e2840` | `#dce3f0` | Nav hover, row hover, subtle highlights |
| Primary | `#00d4b4` | `#00b89c` | Interactive elements, active nav indicator, links, focus ring |
| Primary foreground | `#0f1117` | `#ffffff` | Text on primary-coloured fills |
| Foreground | `#ffffff` | `#1a1f2e` | Headings, body copy, icon fills |
| Muted foreground | `#8b92a5` | `#5c6478` | Secondary text, placeholders, inactive nav labels |
| Border | `#252b3b` | `#c8d0e0` | Dividers, card outlines, input borders |
| Input surface | `#111623` | `#f4f6fb` | Text inputs, selects, code blocks |

### Dark Mode Palette

| Role | Name | Hex |
|------|------|-----|
| Page background | Void | `#0f1117` |
| Surface | Navy | `#1a1f2e` |
| Accent surface | Navy-light | `#1e2840` |
| Primary | Teal | `#00d4b4` |
| Foreground | White | `#ffffff` |
| Muted foreground | Slate | `#8b92a5` |
| Border | Dim | `#252b3b` |
| Input surface | Pit | `#111623` |

```css
.dark {
  --color-background:           #0f1117;
  --color-foreground:           #ffffff;
  --color-card:                 #1a1f2e;
  --color-card-foreground:      #ffffff;
  --color-popover:              #1a1f2e;
  --color-popover-foreground:   #ffffff;
  --color-primary:              #00d4b4;
  --color-primary-foreground:   #0f1117;
  --color-secondary:            #252b3b;
  --color-secondary-foreground: #ffffff;
  --color-muted:                #252b3b;
  --color-muted-foreground:     #8b92a5;
  --color-accent:               #1e2840;
  --color-accent-foreground:    #ffffff;
  --color-border:               #252b3b;
  --color-input:                #111623;
  --color-ring:                 #00d4b4;
}
```

### Light Mode Palette

| Role | Name | Hex |
|------|------|-----|
| Page background | White | `#ffffff` |
| Surface | Frost | `#e8edf5` |
| Accent surface | Mist | `#dce3f0` |
| Primary | Teal-deep | `#00b89c` |
| Foreground | Navy | `#1a1f2e` |
| Muted foreground | Stone | `#5c6478` |
| Border | Haze | `#c8d0e0` |
| Input surface | Pale | `#f4f6fb` |

The primary teal is deepened from `#00d4b4` to `#00b89c` in light mode so it holds sufficient contrast against pale surfaces. All interactive states (focus rings, active nav, primary buttons) use this deeper value.

```css
:root {
  --color-background:           #ffffff;
  --color-foreground:           #1a1f2e;
  --color-card:                 #e8edf5;
  --color-card-foreground:      #1a1f2e;
  --color-popover:              #e8edf5;
  --color-popover-foreground:   #1a1f2e;
  --color-primary:              #00b89c;
  --color-primary-foreground:   #ffffff;
  --color-secondary:            #dce3f0;
  --color-secondary-foreground: #1a1f2e;
  --color-muted:                #dce3f0;
  --color-muted-foreground:     #5c6478;
  --color-accent:               #dce3f0;
  --color-accent-foreground:    #1a1f2e;
  --color-border:               #c8d0e0;
  --color-input:                #f4f6fb;
  --color-ring:                 #00b89c;
}
```

### Severity Colours

Severity colours are the only place warm/saturated hues appear. They are never used in brand elements or decorative UI.

Severity badges use a **ghost/tinted variant**: a low-opacity background (15%), coloured text, and a faint coloured border. This preserves semantic colour without dominating the row against the dark palette. The base hues are the same in both modes; increase opacity to `/20` in light mode if contrast is insufficient.

| Severity | Hue | Tailwind classes |
|----------|-----|-----------------|
| CRITICAL | Red | `bg-red-600/15 text-red-400 border border-red-600/30` |
| HIGH | Orange | `bg-orange-600/15 text-orange-400 border border-orange-600/30` |
| MEDIUM | Amber | `bg-amber-600/15 text-amber-400 border border-amber-600/30` |
| LOW | Blue | `bg-blue-600/15 text-blue-400 border border-blue-600/30` |
| UNKNOWN | Slate | `bg-gray-600/15 text-gray-400 border border-gray-600/30` |

### Finding Status Colours

Finding status badges represent **workflow state**, not danger level. They must never reuse severity hues (red, orange, amber) — those are reserved for severity badges and destructive actions. Each status uses a distinct hue with the same ghost/tinted treatment as severity badges.

| Status | Hue | Tailwind classes | Meaning |
|--------|-----|-----------------|---------|
| Active | Sky | `bg-sky-600/15 text-sky-400 border border-sky-600/30` | Finding is open and unaddressed |
| Fixed | Green | `bg-green-700/15 text-green-400 border border-green-700/30` | Vulnerability has been patched |
| Accepted | Violet | `bg-violet-600/15 text-violet-400 border border-violet-600/30` | Risk acknowledged and accepted |
| False Positive | Slate | `bg-gray-600/15 text-gray-400 border border-gray-600/30` | Dismissed as not applicable |

### Agent Status Colours

Agent status badges use the same ghost/tinted treatment as severity and finding status badges. `scanning` uses the CSS primary variable so it automatically tracks the mode-appropriate teal.

| Status | Hue | Tailwind classes | Meaning |
|--------|-----|-----------------|---------|
| Online | Green | `bg-green-600/15 text-green-400 border border-green-600/30` | Agent connected, idle |
| Scanning | Teal | `bg-primary/15 text-primary border border-primary/30` | Active scan in progress |
| Offline | Red | `bg-red-600/15 text-red-400 border border-red-600/30` | Agent disconnected |

### Teal Glow (use sparingly)

A radial teal wash may appear behind key status indicators (e.g. the scanning state pulse). Use `#00d4b4` at 10% opacity in dark mode; `#00b89c` at 8% opacity in light mode. Never apply to cards, table rows, or decorative elements.

---

## Typography

### Fonts

| Role | Font | Fallback |
|------|------|---------|
| UI / body | [Inter](https://rsms.me/inter/) | `system-ui, sans-serif` |
| Data / monospace | [JetBrains Mono](https://www.jetbrains.com/lp/mono/) | `ui-monospace, monospace` |

Inter covers navigation, labels, body copy, and dialog text. JetBrains Mono is used for CVE IDs, package versions, hashes, and container image tags — any data that benefits from fixed-width alignment.

### Scale

| Token | Size | Weight | Usage |
|-------|------|--------|-------|
| `text-xs` | 12px | 400 | Table metadata, timestamps, badge labels |
| `text-sm` | 14px | 400 / 500 | Body, nav labels, form labels |
| `text-base` | 16px | 400 | Dialog body, descriptions |
| `text-lg` | 18px | 600 | Card titles, section headings |
| `text-xl` | 20px | 600 | Page headings |
| `text-2xl` | 24px | 700 | Dashboard stat numbers |

### Letter Spacing

Navigation labels and the wordmark use `tracking-wide` (+0.05em). All other text uses default tracking.

### Hierarchy Rule

Never use more than three text weights on a single page (400 for body, 500 for labels, 600–700 for headings). Hierarchy is created through weight, size, and muted colour — not through font style or colour variation.

---

## Layout

### App Shell

```
┌──────────────────────────────────────────────┐
│ Sidebar (w-56, fixed) │ Main content          │
│                       │ (flex-1, overflow-y)  │
│  Logo / wordmark      │                       │
│  ─────────────────    │  Page heading         │
│  Nav items            │  ─────────────────    │
│                       │  Content              │
│  ─────────────────    │                       │
│  Theme toggle         │                       │
│  Log out              │                       │
└──────────────────────────────────────────────┘
```

- **Sidebar**: `bg-card border-r border-border`. Width fixed at `w-56`. In dark mode the sidebar is navy against a void canvas; in light mode it is frost against white — the contrast relationship is the same.
- **Main content**: `p-8` padding. Max-width is unconstrained — tables fill available space.
- **Page heading**: `text-xl font-semibold` with an optional subtitle in `text-muted-foreground text-sm` below.

### Spacing

Use Tailwind's 4px base unit throughout. Common spacings:

| Use | Token |
|-----|-------|
| Between page sections | `space-y-6` |
| Card internal padding | `p-4` or `p-6` |
| Inline gap (icon + label) | `gap-2` or `gap-3` |
| Table cell padding | `px-4 py-3` |
| Form field gap | `space-y-4` |

### Border Radius

| Component | Radius |
|-----------|--------|
| Cards, dialogs | `rounded-lg` (8px) |
| Buttons, inputs | `rounded-md` (6px) |
| Badges | `rounded` (4px) |
| Pill variants (rare) | `rounded-full` |

---

## Components

### Navigation

Active nav items use `bg-accent text-accent-foreground`. Inactive items use `text-muted-foreground` and transition to `hover:bg-accent hover:text-accent-foreground` on hover. Icons are `h-4 w-4` (16px) from `lucide-react`.

In light mode the accent surface (`#dce3f0`) is a cooler blue-grey — the same structural role as dark mode's navy-light. The teal active indicator is not shown as a separate ring; the filled background is sufficient.

### Cards

Use `<Card>` from shadcn for all grouping surfaces. Cards sit one layer above the page canvas in both modes (navy on void / frost on white), creating subtle depth without explicit drop shadows.

- Do not add `shadow-*` classes. Elevation is implied by colour contrast alone.
- A `border border-border` gives crisp definition. In light mode this border (`#c8d0e0`) provides the separation that the colour contrast handles in dark mode.

### Buttons

| Variant | Dark appearance | Light appearance | When to use |
|---------|----------------|-----------------|-------------|
| Default | `#00d4b4` fill, dark text | `#00b89c` fill, white text | Primary action per page (one maximum) |
| Secondary | Navy fill, white text | Mist fill, navy text | Secondary and supporting actions |
| Outline | Transparent, dim border | Transparent, haze border | Tertiary actions, filters |
| Ghost | No border/fill | No border/fill | Navigation, icon-only controls |
| Destructive | Red fill, white text | Red fill, white text | Irreversible actions (delete, revoke) |

Button labels are sentence-case. Icon buttons must have a `title` attribute for accessibility.

### Data Tables

- Header row: `text-muted-foreground text-xs uppercase tracking-wide`. Never use the foreground colour for headers.
- Row hover: `hover:bg-accent/50` (50% accent, not full).
- Clickable rows use `cursor-pointer`.
- Columns with numeric/ID data use `font-mono text-xs` (JetBrains Mono).
- Severity and status columns are left-aligned with other text columns.
- Empty state: centred, muted icon + `text-muted-foreground` explanation. Never a raw "No data" string.

### Badges

All badges use the `<Badge>` component. They are small and use sharp radius (`rounded`). Text is always `text-xs font-medium uppercase`.

All status and severity badges use a **ghost/tinted style**: low-opacity background (15%), coloured text, and a faint coloured border (30%). This keeps the palette readable without overwhelming the dark surface. Do not use solid fills for these badges. See the Severity Colours, Finding Status Colours, and Agent Status Colours sections for per-value Tailwind classes.

### Forms & Inputs

- Labels: `text-sm font-medium text-foreground` above the input.
- Helper/description text: `text-sm text-muted-foreground` below.
- Error text: `text-sm text-destructive-foreground`.
- Inputs have `bg-input border border-border` and focus ring in the mode-appropriate primary teal (`ring-primary`).
- All form dialogs use a `<Dialog>` with a descriptive `<DialogDescription>`.

### Dialogs

- Title: `text-lg font-semibold`.
- Description: `text-sm text-muted-foreground` immediately below the title.
- Actions sit in `<DialogFooter>` with Cancel (outline) on the left, primary action on the right.
- Destructive confirmation dialogs use a red primary button and a plain-language description of consequences.

---

## Iconography

Source: `lucide-react`. All icons are `h-4 w-4` (16px) inline with text, or `h-5 w-5` (20px) standalone in empty states.

Icon colour inherits from text colour by default. Do not apply explicit colour to icons unless they carry independent semantic meaning (e.g. a teal scan icon in the scanning state).

Do not use icons purely for decoration. Every icon must accompany a label or have an accessible title.

---

## Interaction & Motion

Trivyal uses minimal animation. The UI is a tool, not a product demo.

- State transitions (hover, focus, active): `transition-colors duration-150` only.
- No slide-in panels, expand/collapse animations, or skeleton loaders in the initial scope.
- Loading states: a simple spinner or `text-muted-foreground` "Loading…" label inline with the content area.
- Toast notifications (if introduced): appear bottom-right, auto-dismiss after 4s, no enter/exit animation beyond a 150ms opacity fade.

---

## Data Visualisation

Dashboard summary cards show counts as large numerals (`text-2xl font-bold`) with a severity colour label below. No donut charts, sparklines, or progress bars in the initial scope — counts and tables are sufficient for a homelab audience.

If charts are introduced later, use a monochrome-first approach: the mode-appropriate teal for the primary series, surface fills for backgrounds, and severity colours only when the data maps directly to a severity level.

---

## Voice & Tone (UI copy)

- Labels and headings: concise, noun-first. "Scan History", "Accept Risk", "Add Agent".
- Empty states: matter-of-fact, actionable. "No findings. Run a scan to get started."
- Confirmation dialogs: explicit about consequences. "This will mark the finding as accepted and suppress future alerts for this CVE on this image."
- Error messages: specific, not apologetic. "Failed to connect to hub. Check your network and try again."
- Never use exclamation marks, emoji, or marketing language.

---

## What to Avoid

- Drop shadows on any element
- Gradients (except the subtle shield gradient in the logo itself)
- Glassmorphism or frosted-glass effects
- More than three hues on any single page (background/surface/primary + severity colours where required)
- Red or orange outside of severity badges and destructive actions
- Decorative illustrations or stock imagery
- Rounded-full pills for severity badges (they should feel sharp, not friendly)
- Pure black (`#000000`) anywhere — the darkest value in light mode is navy (`#1a1f2e`)
- Pure white (`#ffffff`) for text in light mode — use navy (`#1a1f2e`) for all foreground
- Light mode as the default — the app always opens in dark mode; light mode is opt-in
