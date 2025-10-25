# Design Guidelines for Nexus RAG Dashboard

## Design Approach: AI Platform Design System

**Rationale**: As an enterprise-grade AI/ML tool for data scientists and engineers, this dashboard prioritizes clarity, information density, and functional efficiency. Drawing inspiration from Vercel, Linear, and DataBricks, we'll create a sophisticated, data-centric interface that balances technical depth with visual refinement.

**Core Principles**:
- Information density over decoration
- Technical precision with visual elegance  
- Dark-first design for extended use
- Modular card-based architecture

---

## Color Palette

**Dark Mode (Primary)**:
- Background: 222 14% 8% (deep charcoal)
- Surface: 222 14% 11% (elevated cards)
- Surface Elevated: 222 14% 14% (hover states, modals)
- Border: 222 14% 18% (subtle separators)
- Text Primary: 210 40% 98% (high contrast)
- Text Secondary: 215 20% 65% (muted labels)

**Light Mode**:
- Background: 0 0% 100%
- Surface: 0 0% 98%
- Border: 220 13% 91%
- Text Primary: 222 47% 11%
- Text Secondary: 215 14% 34%

**Semantic Colors**:
- Primary (Brand): 221 83% 53% (vibrant blue for CTAs, active states)
- Success: 142 76% 36% (green for completed tasks, health indicators)
- Warning: 38 92% 50% (amber for alerts)
- Error: 0 84% 60% (red for failures, critical states)
- Info: 199 89% 48% (cyan for informational badges)

**Data Visualization Palette**: 221 83% 53%, 142 76% 36%, 271 81% 56%, 24 95% 53%, 199 89% 48%

---

## Typography

**Font Stack**:
- Primary: Inter (Google Fonts) - body text, UI elements
- Monospace: JetBrains Mono (Google Fonts) - code, technical data, JSON

**Scale**:
- Headings: font-semibold tracking-tight
- H1: text-3xl (dashboard titles)
- H2: text-2xl (section headers)  
- H3: text-xl (card titles)
- Body: text-sm (default), text-xs (labels, captions)
- Code: font-mono text-sm (technical data)

---

## Layout System

**Spacing Primitives**: Use Tailwind units of 1, 2, 3, 4, 6, 8, 12, 16, 20, 24 for consistent rhythm.

**Grid Foundation**:
- Main container: max-w-7xl mx-auto px-4 sm:px-6 lg:px-8
- Card padding: p-6 (desktop), p-4 (mobile)
- Section spacing: space-y-6 between major sections
- Grid layouts: grid gap-4 md:gap-6 for card arrangements

**Responsive Breakpoints**:
- Mobile: Single column stack
- Tablet (md:): 2-column grids for stats, 1-column for complex tables
- Desktop (lg:): Multi-column layouts, side panels, split views

---

## Component Library

### Navigation
- **Sidebar Navigation**: Fixed left sidebar (w-64) with icon + label menu items, collapsible on mobile
- **Top Bar**: Breadcrumbs, search, user profile, theme toggle
- Active state: Primary blue background with white text
- Hover: Surface elevated background

### Cards & Panels
- **Elevated Cards**: Rounded-lg border with subtle shadow on dark mode
- **Stats Cards**: Grid of metric cards with large numbers, trend indicators (↑↓ arrows with color)
- **Sectioned Cards**: Header with title + action button, body with content, optional footer

### Data Display
- **Tables**: Striped rows (alternate bg), sticky headers, row hover states, inline actions
- **Charts**: Recharts with brand color palette, grid lines at 215 20% 25%, tooltips with dark surface background
- **Code Blocks**: Monospace font, syntax highlighting via Prism.js, copy button in top-right

### Forms & Inputs
- **Input Fields**: Border style, focus ring in primary color, labels above inputs
- **File Upload**: Drag-drop zone with dashed border, file preview cards
- **Sliders**: Custom range inputs for parameters (top_k, temperature) with live value display
- **Toggles**: Switch components for boolean settings

### Interactive Elements
- **Primary Buttons**: bg-primary text-white, hover brightness increase
- **Secondary Buttons**: variant="outline" with border, hover bg-surface-elevated
- **Buttons on Images**: variant="outline" with backdrop-blur-sm bg-surface/10
- **Icon Buttons**: Ghost variant for actions, size-8 with size-4 icons
- **Loading States**: Skeleton screens using animate-pulse, spinners for async actions

### Modals & Overlays
- **Dialogs**: Centered modal with backdrop, max-w-2xl for forms, max-w-4xl for data views
- **Toasts**: Top-right notifications with icons, auto-dismiss
- **Dropdowns**: Radix Select components with custom styling

---

## Feature-Specific Design

### Dashboard Home
- **Layout**: 3-column stat grid (queries, docs, embeddings), followed by 2-column (recent activity + quick actions)
- **Charts**: Line chart for query volume (last 7 days), bar chart for top document groups

### Document Management  
- **Table View**: Name, upload date, size, chunk count, status badge, action menu
- **Upload Zone**: Large drag-drop area with file type icons, progress bars during upload
- **Document Groups**: Tag-style pills for filtering, color-coded by category

### Query Interface
- **Split View**: Left panel (query input + parameters), right panel (response + retrieved chunks)
- **Chat History**: Timeline style with alternating user/assistant messages
- **Parameter Controls**: Collapsible panel with labeled sliders and number inputs

### Embedding & Vector Store
- **Health Dashboard**: Large circular progress for index health, grid of key metrics
- **Preview Panel**: Code block showing sample vectors, similarity scores as percentage bars

### Fine-Tuning
- **Wizard Flow**: Step indicator at top, forms in cards, progress tracked via stepper component
- **Training Monitor**: Real-time metrics with line charts, logs in scrollable terminal-style box

---

## Animations

**Minimal Approach**: Use sparingly for feedback only
- Page transitions: Fade in (200ms)
- Card hover: Scale 1.01 + shadow increase (150ms)
- Loading: Pulse on skeletons, spin on icons
- No complex scroll animations or parallax

---

## Images

**Hero Section**: Not applicable - dashboard opens directly to functional interface

**Illustrations**:
- Empty states: Simple line illustrations for "No documents uploaded" or "No queries yet"
- Onboarding: Optional small icons for feature explanations
- Avatars: User profile images in top-right navigation

---

## Accessibility & Quality

- WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large)
- Keyboard navigation with visible focus rings (ring-2 ring-primary)
- Screen reader labels on icon buttons
- Consistent dark mode across all inputs and overlays
- Reduced motion respect via prefers-reduced-motion

---

## Icon Library

Use **Lucide React** exclusively for consistent icon language across all UI elements.