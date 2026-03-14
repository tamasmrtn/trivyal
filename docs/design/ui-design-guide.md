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

### Contrast Ratios (WCAG 2.1 AA)

All text combinations must meet at minimum **4.5:1** for body text (AA), **3:1** for large text (18px+ or bold 14px+). The palettes above are designed to satisfy these ratios in both modes — do not substitute random values.

| Pair | Ratio (dark) | Ratio (light) | Passes |
|------|-------------|--------------|--------|
| Foreground on Background | ~15:1 | ~14:1 | AAA |
| Muted foreground on Background | ~5.5:1 | ~4.6:1 | AA |
| Primary teal on Background | ~8:1 | ~4.7:1 | AA |
| Foreground on Card | ~12:1 | ~10:1 | AAA |

---

## Typography

### Fonts

| Role | Font | Fallback |
|------|------|---------|
| UI / body | [Inter](https://rsms.me/inter/) | `system-ui, sans-serif` |
| Data / monospace | [JetBrains Mono](https://www.jetbrains.com/lp/mono/) | `ui-monospace, monospace` |

Inter covers navigation, labels, body copy, and dialog text. JetBrains Mono is used for CVE IDs, package versions, hashes, container image tags, and any copy-paste tokens — any data that benefits from fixed-width alignment or scannability.

### Scale

| Token | Size | Weight | Usage |
|-------|------|--------|-------|
| `text-xs` | 12px | 400 | Table metadata, timestamps, badge labels |
| `text-sm` | 14px | 400 / 500 | Body, nav labels, form labels |
| `text-base` | 16px | 400 | Dialog body, descriptions |
| `text-lg` | 18px | 600 | Card titles, section headings |
| `text-xl` | 20px | 600 | Page headings (standard) |
| `text-2xl` | 24px | 700 | Dashboard stat numbers, hero KPIs |

### Letter Spacing

Navigation labels and the wordmark use `tracking-wide` (+0.05em). All other text uses default tracking.

### Hierarchy Rule

Never use more than three text weights on a single page (400 for body, 500 for labels, 600–700 for headings). Hierarchy is created through weight, size, and muted colour — not through font style or colour variation.

### Monospace Usage

Apply `font-mono text-xs` (JetBrains Mono) to:
- CVE IDs (`CVE-2024-12345`)
- Package names and versions
- Container image tags and digests
- Hub public keys and registration tokens
- Docker Compose environment variable values in copy-paste snippets

---

## Layout

### App Shell

```
┌──────────────────────────────────────────────┐
│ Sidebar (w-56, fixed) │ Main content          │
│                       │ (flex-1, overflow-y)  │
│  Logo / wordmark      │                       │
│  ─────────────────    │  Page header          │
│  Nav items            │  ─────────────────    │
│                       │  Content              │
│  ─────────────────    │                       │
│  Theme toggle         │                       │
│  Log out              │                       │
└──────────────────────────────────────────────┘
```

- **Sidebar**: `bg-card border-r border-border`. Width fixed at `w-56`. In dark mode the sidebar is navy against a void canvas; in light mode it is frost against white.
- **Main content**: `p-6 sm:p-8` padding. Max-width is unconstrained — tables fill available space.
- **Page header**: standard pattern — see Page Header section below.

### Responsive Breakpoints

Trivyal is primarily a desktop tool (operators use it at a workstation), but must remain fully functional on tablet and readable on mobile for on-call situations.

| Breakpoint | Width | Layout change |
|-----------|-------|--------------|
| `sm` | 640px | Two-column grids collapse to one column |
| `md` | 768px | Filter controls may wrap |
| `lg` | 1024px | Sidebar visible (desktop layout) |

**Mobile (< 1024px):** The sidebar collapses into a `Sheet` (slide-in drawer from left). A hamburger menu button appears in a top bar. The main content fills the full width. All pages must be usable without horizontal scroll at 375px viewport width.

**Column grids:** Use `grid-cols-1 sm:grid-cols-2 lg:grid-cols-N` for all card grids. Dashboard summary cards use `sm:grid-cols-2 lg:grid-cols-5`.

### Page Header

Every page uses a consistent header row at the top of the main content area:

```
┌────────────────────────────────────────────┐
│ h1 (page title)  [optional context badge]  │
│                                [controls]  │
└────────────────────────────────────────────┘
```

```tsx
<div className="mb-6 flex flex-wrap items-center justify-between gap-4">
  <div className="flex items-center gap-3">
    <h1 className="text-2xl font-bold">{title}</h1>
    {contextBadge && <span className="bg-muted rounded-md px-2 py-1 text-sm">{contextBadge}</span>}
  </div>
  <div className="flex flex-wrap items-center gap-3">
    {/* filters, toggles, actions */}
  </div>
</div>
```

- Page title: `text-2xl font-bold` (not `text-xl` — the heading scale in this guide uses `text-xl` for section headings, `text-2xl` for the page-level h1)
- Context badge (e.g. image name filter active on Findings): `bg-muted rounded-md px-2 py-1 text-sm`
- Controls wrap on mobile via `flex-wrap gap-3`

### Spacing

Use Tailwind's 4px base unit throughout. Common spacings:

| Use | Token |
|-----|-------|
| Between page sections | `space-y-6` or `mt-8` |
| Card internal padding | `p-4` or `p-6` |
| Inline gap (icon + label) | `gap-2` or `gap-3` |
| Table cell padding | `px-4 py-3` |
| Form field gap | `space-y-4` |
| Between filter controls | `gap-3` |
| Page header to content | `mb-6` |

### Border Radius

| Component | Radius |
|-----------|--------|
| Cards, dialogs | `rounded-lg` (8px) |
| Buttons, inputs, selects | `rounded-md` (6px) |
| Badges | `rounded` (4px) |
| Pill variants (rare) | `rounded-full` |

---

## Components

### Navigation

**Sidebar nav items:**
- Active: `bg-accent text-accent-foreground font-medium`
- Inactive: `text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors`
- Icons: `h-4 w-4` Lucide icons, `mr-2` gap from label
- The teal primary colour is **not** used as a fill on active nav items — `bg-accent` is sufficient. The active teal appears only in focus rings and primary buttons.

**Mobile nav:** rendered as a `Sheet` component with `side="left"`. The drawer slides in over the content; the rest of the page is dimmed with a scrim overlay. Tap outside or press Escape to close.

**Nav item order (top to bottom):**
1. Dashboard
2. Priorities
3. Findings
4. Agents
5. Insights
6. Scan History

Theme toggle and log out sit at the bottom of the sidebar, separated by a visual divider (`border-t border-border mt-auto`).

### Cards

Use `<Card>` from shadcn for all grouping surfaces.

- Do not add `shadow-*` classes. Elevation is implied by colour contrast alone.
- Add `border border-border` for crisp definition. In light mode this border provides the separation that colour contrast handles in dark mode.
- **Clickable cards** (e.g. Dashboard shortcut cards): add `cursor-pointer hover:border-primary/50 transition-colors role="link" tabIndex={0}` and a keyboard handler for Enter/Space.
- Card header with icon: use `flex flex-row items-center justify-between pb-2` in `<CardHeader>`.

### Buttons

| Variant | Dark appearance | Light appearance | When to use |
|---------|----------------|-----------------|-------------|
| Default | `#00d4b4` fill, dark text | `#00b89c` fill, white text | Primary action per page (one maximum) |
| Secondary | Navy fill, white text | Mist fill, navy text | Secondary and supporting actions |
| Outline | Transparent, dim border | Transparent, haze border | Tertiary actions, filter toggles |
| Ghost | No border/fill | No border/fill | Navigation, icon-only controls |
| Destructive | Red fill, white text | Red fill, white text | Irreversible actions (delete, revoke) |

- Button labels are sentence-case.
- Icon-only buttons must have a `title` attribute or an `aria-label`.
- Active filter toggle buttons use `cn(active && "bg-primary text-primary-foreground")` on top of the `outline` variant.
- Use `size="sm"` for controls in the page header row to keep the header compact.
- Disable buttons during async operations and show a spinner via a `disabled` prop — never leave the UI unresponsive after a click.

### Data Tables

- Header row: `text-muted-foreground text-xs uppercase tracking-wide font-medium`
- Row hover: `hover:bg-accent/50`
- Clickable rows: `cursor-pointer`
- Numeric/ID columns: `font-mono text-xs` (JetBrains Mono)
- Severity and status badge columns: left-aligned with text columns
- **Sortable columns**: show a sort direction chevron icon (`ChevronUp` / `ChevronDown` from lucide, `h-4 w-4`) inline after the header label. Unsorted columns show a neutral `ChevronsUpDown` icon at reduced opacity (`opacity-40`). Clicking a sorted column reverses direction; clicking an unsorted column sorts descending first.
- **Empty state**: centred inside the table body, minimum 200px height, using the empty state pattern (see Empty States section).
- **Table wrapper**: use `rounded-lg border overflow-hidden` so the table corners and border match card corners.

### Pagination

Used on Findings and Scan History. Sits below the table with `mt-4 flex items-center justify-between`.

```
12 findings total         [Previous]  Page 2 of 4  [Next]
```

- Count text: `text-sm text-muted-foreground` on the left
- Buttons: raw `<button>` with `rounded-md border px-3 py-2 text-sm hover:bg-accent transition-colors disabled:opacity-50` — do not use the Button component (it adds extra height)
- Page indicator: `text-sm text-muted-foreground px-2 py-1`
- Hide the pagination row entirely when `totalPages <= 1`

### Badges

All badges use the `<Badge>` component. They are small and use sharp radius (`rounded`). Text is always `text-xs font-medium uppercase`.

All status and severity badges use a **ghost/tinted style**: low-opacity background (15%), coloured text, and a faint coloured border (30%). This keeps the palette readable without overwhelming the dark surface. Do not use solid fills for these badges. See the Colour Palette section for per-value Tailwind classes.

### Filter Controls

Filters appear in the page header row, laid out with `flex flex-wrap items-center gap-3`.

**Dropdown selects** (agent filter, sort): native `<select>` with `bg-input text-foreground border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-ring focus:outline-none`. This matches input styling exactly.

**Segmented / toggle buttons** (severity, status): outlined `<Button>` with active state: `cn(active && "bg-primary text-primary-foreground")`. Group these horizontally with `gap-1` inside a `flex` container.

**Toggle switch** (Fixable only): an outline Button that becomes teal when active. Label: "Fixable only". Always right-most in the controls row.

**Active filter indicator**: when filters are applied from an external context (e.g. Findings opened from Priorities with an image name), show a context badge next to the page title (see Page Header section). Clicking it clears that filter.

When filter state is non-trivial (many combinations possible), all filter controls live in the page header row — not in a sidebar or drawer. This keeps the interaction model simple and the table full-width.

### Forms & Inputs

- Labels: `text-sm font-medium text-foreground` above the input
- Helper/description text: `text-sm text-muted-foreground` below the input
- Error text: `text-sm text-destructive-foreground`
- Inputs: `bg-input border border-border rounded-md` with focus ring `focus:ring-2 focus:ring-ring focus:outline-none`
- All form dialogs use a `<Dialog>` with a descriptive `<DialogDescription>`
- Required fields: mark with a trailing asterisk in the label (`*`), not inline placeholder text
- Validate on blur; display error text below the field immediately after
- Long-form text areas (reason for risk acceptance): `min-h-[80px] resize-y`

### Dialogs

- Title: `text-lg font-semibold`
- Description: `text-sm text-muted-foreground` immediately below the title, inside `<DialogDescription>`
- Actions in `<DialogFooter>`: Cancel (outline) on the left, primary action on the right
- Destructive confirmation dialogs: red `destructive` variant primary button; plain-language description of consequences in the body
- Default dialog width: shadcn default (`sm:max-w-lg`). Never wider than `max-w-2xl`.
- Do not stack multiple dialogs. A dialog triggered from within a dialog is a design smell — flatten into a single flow.

### Code Blocks & Copy-paste Snippets

Used for registration tokens, hub public keys, and Docker Compose snippets.

- Surface: `bg-input border border-border rounded-md`
- Text: `font-mono text-xs text-foreground`
- Padding: `p-3`
- Copy button: positioned top-right inside the block, `ghost` variant with a `Copy` Lucide icon and `title="Copy to clipboard"`. After copy, swap to a `Check` icon for 2 seconds, then revert.
- Long tokens that may wrap: use `break-all` on the text.

Example:

```tsx
<div className="relative">
  <pre className="bg-input border rounded-md p-3 font-mono text-xs text-foreground overflow-x-auto">
    {tokenValue}
  </pre>
  <Button
    variant="ghost"
    size="icon"
    className="absolute top-2 right-2 h-6 w-6"
    onClick={handleCopy}
    title="Copy to clipboard"
  >
    {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
  </Button>
</div>
```

### Inline Alerts

For page-level error states that are recoverable (e.g. failed to load findings):

```
┌──────────────────────────────────────────────────┐
│  ⚠ Failed to load findings. [Retry]              │
└──────────────────────────────────────────────────┘
```

- Container: `flex items-center gap-3 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm`
- Icon: `AlertCircle` from lucide, `h-4 w-4 text-destructive-foreground shrink-0`
- Message: `text-foreground`
- Retry: ghost `<Button size="sm">Retry</Button>` inline

This is preferred over centred full-page error text for most data-loading failures, as it allows the page chrome (header, sidebar) to remain visible.

Full-page error (used only for auth failures or route-not-found):

```tsx
<div className="flex h-64 items-center justify-center">
  <p className="text-destructive-foreground">{error}</p>
</div>
```

---

## Iconography

Source: `lucide-react`. All icons are:
- `h-4 w-4` (16px) inline with text or in table/badge contexts
- `h-5 w-5` (20px) standalone in empty states or as primary page-level icon
- `h-6 w-6` (24px) never — too large for this UI density

Icon colour inherits from text colour by default. Do not apply explicit colour unless the icon carries independent semantic meaning (e.g. a teal `Activity` icon in scanning state, a red `AlertTriangle` icon in an error state).

Do not use icons purely for decoration. Every icon must accompany a label or have an accessible `title` attribute.

**Icon ↔ feature mapping:**

| Feature | Icon |
|---------|------|
| Dashboard | `LayoutDashboard` |
| Priorities / Fix Today | `Wrench` |
| Fixable CVEs / Update | `ArrowUpCircle` |
| Findings | `ShieldAlert` |
| Agents | `Server` |
| Insights | `BarChart2` |
| Scan History | `History` |
| Scan trigger | `Play` or `RefreshCw` |
| Delete / Remove | `Trash2` |
| Copy | `Copy` |
| Success copy | `Check` |
| External link | `ExternalLink` |
| Chevron sort | `ChevronUp` / `ChevronDown` / `ChevronsUpDown` |
| Info / detail | `Info` |
| Error / alert | `AlertCircle` |

---

## State Patterns

### Loading State

Use **skeleton loaders** — never a page-level spinner or a blocking "Loading…" overlay.

Skeleton loaders match the shape of the content they replace:
- Card heading: `<Skeleton className="h-4 w-20 mb-4" />`
- Card stat: `<Skeleton className="h-8 w-12" />`
- Table row cells: `<Skeleton className="h-4 w-[width]" />` (vary widths to look natural)
- Table row wrapper: `flex gap-4 border-b px-4 py-3 last:border-0`
- Render 6–8 skeleton rows for tables

Skeleton colour inherits from shadcn's `<Skeleton>` component which uses `bg-muted` — correct for both modes.

### Error State

**Inline alert** (recoverable, data failed to load):

```tsx
<div className="flex items-center gap-3 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm">
  <AlertCircle className="h-4 w-4 text-destructive-foreground shrink-0" />
  <span>{message}</span>
  <Button variant="ghost" size="sm" onClick={onRetry}>Retry</Button>
</div>
```

**Centred error** (auth failure, fatal error only):

```tsx
<div className="flex h-64 items-center justify-center">
  <p className="text-destructive-foreground">{error}</p>
</div>
```

### Empty State

Used in table bodies and sections when there is no data.

Structure: centred content, minimum height 200px, icon + heading + description + optional action.

```tsx
<div className="flex flex-col items-center justify-center py-16 text-center">
  <Icon className="mb-3 h-8 w-8 text-muted-foreground/40" />
  <p className="text-sm font-medium text-muted-foreground">{heading}</p>
  <p className="mt-1 text-xs text-muted-foreground/70">{description}</p>
  {action && <Button variant="outline" size="sm" className="mt-4">{action}</Button>}
</div>
```

Examples:
- Findings (no results with active filters): icon `Filter`, heading "No findings match your filters", description "Try clearing some filters."
- Findings (no data at all): icon `ShieldCheck`, heading "No findings", description "Run a scan to get started."
- Agents (empty): icon `Server`, heading "No agents registered", description "Add an agent to start scanning."

---

## Interaction & Motion

Trivyal uses minimal animation. The UI is a tool, not a product demo.

- **State transitions** (hover, focus, active): `transition-colors duration-150` only.
- **No slide-in panels, expand/collapse animations** in the main content area. **Exception:** the mobile navigation `Sheet` uses a left-side slide animation — this is appropriate and exempt from this rule.
- **Scanning pulse animation**: the scanning status indicator uses a CSS `animate-pulse` ring around the status dot. Keep it subtle — `ring-1 ring-primary/30 animate-pulse`.
- **Copy success feedback**: swap the `Copy` icon to `Check` instantly (no animation) for 2 seconds, then revert. `transition-opacity duration-150` on the swap is acceptable.
- **Sort column click**: no animation — the table re-renders immediately.
- **Toast notifications**: appear bottom-right via the shadcn `Sonner` or `Toast` component. Auto-dismiss after 4 seconds. No enter/exit animation beyond a 150ms opacity fade. Keep toast messages to one sentence. Do not use toasts for destructive confirmation — use a dialog instead.
- **Dialog open/close**: shadcn default animations are acceptable (`fade + slight scale`). Do not override them.

---

## Data Visualisation

### Dashboard Summary Cards

Summary KPI cards show counts as large numerals (`text-2xl font-bold`) with a label below in `text-sm text-muted-foreground`. The severity colour appears only in the label text or a small inline badge — never as the card background.

```
┌─────────────────────┐
│ CRITICAL            │
│ 12                  │
│ active findings     │
└─────────────────────┘
```

Cards sit in a `grid gap-4 sm:grid-cols-2 lg:grid-cols-5` grid. Each card is clickable and navigates to the Findings page pre-filtered to that severity.

### Insights Charts (Recharts)

The Insights page uses multiple chart types. All charts follow these shared rules:

**Colours:**
- Primary data series: `var(--color-primary)` (teal)
- Severity series: use the exact severity colours from the Severity Colours table — never substitute other colours for severity data
- Per-agent series: a fixed 8-colour palette of desaturated hues that are distinct from severity colours and from teal. Suggested palette: `["#6366f1", "#f59e0b", "#10b981", "#f43f5e", "#8b5cf6", "#06b6d4", "#84cc16", "#fb923c"]`
- Background: transparent (charts sit on card surface)
- Grid lines: `stroke="#252b3b"` (dark) / `stroke="#c8d0e0"` (light) — match border token
- Axis text: `fill` set to muted foreground hex value

**Grid and axes:**
- Show `CartesianGrid` with `strokeDasharray="3 3"` and low-opacity stroke
- X-axis: date labels, `tick={{ fontSize: 12 }}`, skip labels on mobile
- Y-axis: integer counts, no decimals
- Both axes use muted foreground colour for labels

**Tooltips:**
- Always show a `<Tooltip>` — never rely on the chart alone to communicate values
- Tooltip container: `bg-card border border-border rounded-md p-2 text-xs shadow-none`
- Do not use recharts' default white tooltip background — it clashes with dark mode

**Legends:**
- Always show a `<Legend>` for multi-series charts
- Position: `bottom`, with `wrapperStyle={{ paddingTop: "16px", fontSize: "12px" }}`

**Responsiveness:**
- Wrap all charts in `<ResponsiveContainer width="100%" height={300}>` (or appropriate height)
- Never hard-code a pixel width

**Chart types in use:**

| Component | Chart type | Notes |
|-----------|-----------|-------|
| `VulnerabilityTrendChart` | Line chart, multi-series by severity | 5 series (CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN); scan event markers as vertical reference lines |
| `NewVsResolvedChart` | Diverging bar chart | New findings = positive (red); resolved = negative (green); bars go in opposite directions from zero axis |
| `AgentTrendChart` | Line chart, per-agent series | 8-colour palette; one line per agent |
| `SeverityDonutChart` | Pie chart (donut) with inner label | Centre label shows total count; legend below with counts per severity |

**Scan event markers** on `VulnerabilityTrendChart`: use Recharts `<ReferenceLine>` with a vertical dashed line in `stroke="var(--color-primary)"` at 20% opacity. Show a small label above the line reading "Scan" in `text-xs text-muted-foreground`. Space these sparingly — if multiple scans occurred on one day, show only one marker.

---

## Page-Level Layout Patterns

### Dashboard

```
[Page header: "Dashboard" | Fixable only toggle]

[Summary section heading]
[5-column KPI card grid: CRITICAL · HIGH · MEDIUM · LOW · UNKNOWN]

[Divider: border-t mt-8 pt-8]

[2-column action card grid]
  [Fix Today card → /priorities]   [Fixable CVEs card → /priorities]
```

KPI cards each navigate to `/findings?severity={level}` on click. The Fix Today and Fixable CVEs cards navigate to `/priorities`.

### Priorities

```
[Page header: "Priorities"]

[Section: "Fix Today" — heading text-lg font-semibold]
[Severity + status filters inline]
[Misconfig findings table]

[Section divider: border-t mt-8 pt-8]

[Section: "Update When You Can" — heading text-lg font-semibold]
[Image CVE table: image name | fixable CVEs | severity breakdown chips | link to Findings]
```

Both sections have their own loading state (skeleton table rows) so they load independently.

### Agents

```
[Page header: "Agents" | [Add Agent] button (primary, right-aligned)]

[Agents table or agent card grid]
  [Per-agent: name, status badge, last seen, host metadata, Scan Now button, Delete button]

[Add Agent dialog: generate token flow]
```

The "Add Agent" dialog is the only dialog triggered from a page-level action button (not from a table row). It uses a multi-step UI: step 1 shows the generated token and hub public key (both copyable); step 2 shows the Docker Compose snippet (copyable). A `Back` link returns to step 1.

### Findings

```
[Page header: "Findings" [image-name badge if filtered] | agent select · severity filters · status filters · Fixable only]

[Findings table: sortable columns]

[Pagination row: N findings total | [Previous] Page X of Y [Next]]
```

When arrived from Priorities (image name in URL param), the image name appears as a context badge next to the heading. A `×` on the badge clears the `image_name` param.

### Finding Detail

```
[Breadcrumb: Findings / CVE-2024-XXXXX]

[Two-column layout (lg:grid-cols-3)]
  [Main: CVE ID · description · package · versions · link to NVD]     [col-span-2]
  [Sidebar: severity badge · status badge · accept risk form / revoke] [col-span-1]

[Affected containers section]
  [Table: container · agent · first seen · last seen]
```

Breadcrumb: `text-sm text-muted-foreground` with a `ChevronRight` separator. No dedicated breadcrumb component needed — inline JSX.

### Insights

```
[Page header: "Insights" | 7d · 30d · 90d window toggle · Fixable only toggle]

[4 KPI summary cards: Active · Crit+High · New · Fix Rate]

[Two charts side-by-side (lg:grid-cols-2)]
  [VulnerabilityTrendChart]   [NewVsResolvedChart]

[Two charts side-by-side]
  [AgentTrendChart]           [SeverityDonutChart]

[TopCvesTable]
```

Time window toggle: three outline buttons (`7d`, `30d`, `90d`) with active state styled as filled teal. Use `gap-1` between buttons, no border separating them into a true segmented control.

### Scan History

```
[Page header: "Scan History" | agent filter select]

[Timeline or table: scan run · agent · container count · finding delta · timestamp]
```

The "diff view" (new/fixed per scan) uses coloured counts inline: new findings in `text-red-400`, fixed in `text-green-400`. Do not use badges here — inline coloured text is sufficient for compact table cells.

### Login

```
[Centred card on full-height page: bg-background]
  [Logo / wordmark]
  [h1: "Sign in"]
  [Username input]
  [Password input]
  [Sign in button (full width, default variant)]
  [Error message if auth failed]
```

Login page has no sidebar, no nav. Pure centred card. `min-h-dvh flex items-center justify-center`.

---

## Accessibility

Trivyal targets WCAG 2.1 Level AA as a minimum. Key requirements:

**Focus management:**
- All interactive elements must show a visible focus ring: `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`
- Never remove focus rings with `outline-none` unless the element handles its own focus style (shadcn components handle this)
- Tab order must match visual reading order
- After a dialog closes, focus returns to the element that opened it

**Keyboard navigation:**
- Dialogs are fully keyboard-navigable (Tab, Shift+Tab, Escape to close, Enter to confirm)
- Clickable cards use `role="link" tabIndex={0}` and respond to Enter and Space
- Table sort controls are buttons, not just click handlers on `<th>`

**Screen reader labels:**
- Icon-only buttons: `aria-label` or `title` attribute
- Filter selects: `aria-label` describing what they filter
- Table: `<table aria-label="Findings">` for major data tables
- Status badges: text is sufficient (uppercase text inside badge is readable by screen readers)

**Colour independence:**
- Severity is communicated by both colour and the text label inside the badge — never by colour alone
- Sortable column direction: communicated by the chevron icon shape, not just colour

**Reduced motion:**
- All `animate-*` classes (scanning pulse, skeleton shimmer) must be wrapped with `motion-safe:animate-*` or tested against `prefers-reduced-motion: reduce`

---

## Voice & Tone (UI copy)

- Labels and headings: concise, noun-first. "Scan History", "Accept Risk", "Add Agent".
- Empty states: matter-of-fact, actionable. "No findings. Run a scan to get started."
- Confirmation dialogs: explicit about consequences. "This will mark the finding as accepted and suppress future alerts for this CVE on this image."
- Error messages: specific, not apologetic. "Failed to connect to hub. Check your network and try again."
- Never use exclamation marks, emoji, or marketing language.
- Number formatting: bare integers for counts (no thousands separator needed at homelab scale). Dates: relative for recent ("2 hours ago"), absolute ISO date for older ("2024-11-03"). Timestamps in table cells use `text-xs text-muted-foreground font-mono`.

---

## What to Avoid

- Drop shadows on any element
- Gradients (except the subtle shield gradient in the logo itself)
- Glassmorphism or frosted-glass effects
- More than three hues on any single page (background/surface/primary + severity colours where required)
- Red or orange outside of severity badges and destructive actions
- Decorative illustrations or stock imagery
- Rounded-full pills for severity badges (they should feel sharp, not friendly)
- Pure black (`#000000`) anywhere — the darkest value is `#0f1117`
- Pure white (`#ffffff`) for text in light mode — use navy (`#1a1f2e`) for all foreground
- Light mode as the default — the app always opens in dark mode; light mode is opt-in
- Emojis as icons — use Lucide SVG icons only
- Multiple primary CTAs per page — one teal button maximum per view
- Hardcoded hex values in component classes — always use CSS variable tokens (via Tailwind semantic names like `text-muted-foreground`, `bg-card`, etc.)
- `outline-none` on focusable elements without an alternative visible focus indicator
- Nested dialogs (dialog opened from within a dialog)
- Horizontal scroll on any page at 375px viewport width
- Placeholder text as a substitute for visible input labels
