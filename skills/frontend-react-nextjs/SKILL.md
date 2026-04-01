---
name: frontend-react-nextjs
description: Build and review modern frontend interfaces with strong HTML, CSS, Tailwind CSS, React, and Next.js practices, with attention to UX, accessibility, performance, and maintainable component design.
metadata: {"clawdbot":{"emoji":"🎨","requires":{"bins":["node"]}}}
---

# Frontend React Next.js

Use this skill when working on frontend apps or UI systems built with HTML, CSS, Tailwind CSS, React, or Next.js.

## Use this skill for

- building or reviewing pages, dashboards, and reusable components
- improving layout, spacing, typography, and responsive behavior
- implementing designs in React or Next.js
- refining Tailwind CSS usage and component structure
- improving accessibility, loading states, forms, and interaction patterns
- debugging hydration, client/server boundaries, or rendering issues
- improving frontend performance and maintainability

## Working approach

### 1. Read the UI structure before changing it

Start by understanding the app shape and conventions:

```bash
rg --files | rg 'package.json|next\\.config|tailwind|postcss|app/|pages/|components/|src/'
rg -n "use client|className=|clsx|cn\\(|tailwind|styled|emotion|framer-motion" .
```

Check:

- whether the app uses the Next.js app router or pages router
- how shared components are organized
- whether Tailwind utilities, CSS modules, or another styling system are already in use
- how forms, data fetching, and loading states are handled
- whether a design system or component library already exists

Follow the existing patterns unless they are clearly causing bugs or maintenance problems.

### 2. Prefer semantic, accessible HTML

Choose elements for meaning first:

- `header`, `main`, `section`, `nav`, `aside`, `footer`
- `button` for actions
- `a` for navigation
- `label` tied to form inputs
- correct heading hierarchy

Always check:

- keyboard access
- visible focus states
- alt text for meaningful images
- label and error associations for form controls
- sufficient contrast for text and controls

### 3. Build responsive layouts intentionally

Use layout primitives clearly:

- Flexbox for one-dimensional layout
- Grid for multi-column or multi-region layout
- container widths and spacing scales that stay consistent
- mobile-first breakpoints

Avoid patching layouts with arbitrary one-off spacing unless the file already follows that style.

### 4. Keep Tailwind readable

When using Tailwind CSS:

- group utilities in a predictable order
- extract repeated patterns into shared components when reuse is real
- prefer design tokens and existing utility conventions over ad hoc values
- avoid very long, duplicated class strings across files

If the repo uses helpers like `cn()` or `clsx`, keep using them.

### 5. Design React components with clear boundaries

Prefer components that:

- do one job well
- accept explicit props
- keep state near where it is used
- separate presentational concerns from data-heavy orchestration when helpful
- avoid unnecessary prop drilling when a local composition pattern works

Do not split components just for the sake of abstraction.

### 6. Respect Next.js server/client boundaries

For Next.js apps:

- use server components by default when interactivity is not needed
- add `'use client'` only where required
- keep browser-only APIs out of server-rendered code
- use route-level loading and error patterns when the app already supports them
- be careful with hydration-sensitive values like time, random output, and window-based logic

### 7. Handle states, not just the happy path

Every UI flow should consider:

- loading
- empty state
- error state
- success feedback
- disabled or pending actions

If a component fetches or mutates data, the user should be able to understand what is happening.

### 8. Protect performance

Prefer performance wins that preserve clarity:

- reduce unnecessary client-side rendering
- avoid over-fetching and duplicated requests
- keep heavy dependencies justified
- optimize images and large lists
- avoid unnecessary rerenders caused by unstable props or excessive top-level state

In Next.js, prefer framework-native patterns for images, routing, and data loading when the project already uses them.

## React and Next.js guidance

### Component structure

- keep JSX easy to scan
- extract subcomponents when they clarify intent or remove duplication
- avoid giant components mixing fetching, business rules, and presentation

### State management

- use local state for local behavior
- lift state only when multiple siblings truly depend on it
- follow the repo's existing state tools instead of introducing a new one casually

### Forms

- validate inputs clearly
- preserve input labels and help text
- show inline errors where users need them
- prevent double submission during pending states

### Data fetching

- match the framework pattern already in place
- avoid mixing several fetching styles on the same screen unless necessary
- make cache or revalidation behavior explicit when it affects UX

## CSS and visual quality defaults

Prefer interfaces that feel deliberate:

- clear type hierarchy
- strong spacing rhythm
- restrained color usage
- consistent border radius, shadows, and density
- motion that supports comprehension instead of distracting from it

When working in an existing product, preserve the design language instead of restyling everything.

## Review checklist

When reviewing frontend code, look for:

- inaccessible interactions or missing semantics
- broken responsive behavior
- hydration or server/client boundary mistakes
- duplicated UI logic that should be centralized
- unclear loading, error, or empty states
- Tailwind sprawl or unmaintainable class composition
- performance regressions from unnecessary client work
- missing tests for interactive or stateful behavior

## Safety rules

- do not convert server-rendered code to client-only code without a reason
- do not introduce a new styling or state library unless it is clearly justified
- do not hide important actions behind hover-only interactions
- do not remove accessibility affordances for visual neatness
- do not mix unrelated UI refactors into a bug fix unless necessary

## Output style

When using this skill:

- explain UX and implementation tradeoffs clearly
- reference the page, component, and state flow involved
- prefer focused improvements over broad rewrites
- call out accessibility and responsive risks explicitly
