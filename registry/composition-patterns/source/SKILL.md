---
name: composition-patterns
description: Enforce well-designed React component composition — compound components, explicit variants, decoupled context, maintainable state models — instead of boolean-prop explosion or render-prop abuse. Use for design systems, component libraries, complex forms, Modal/Dropdown/Select/Tabs-style composable components.
---

# composition-patterns

When the user asks you to design or refactor React components, apply these rules **before** writing code:

## Red flags to detect

- **Boolean prop explosion**: `<Modal isOpen isLarge isCentered hasOverlay hasCloseButton ...>` → use **compound components** or **variants**
- **Configuration prop bag**: `<Select options={{...30 keys...}}>` → use **slots / subcomponents**
- **render-props for trivial cases**: `<Provider render={x => <Inner x={x} />}>` → use **hooks** or **context**
- **Implicit state ownership**: parent and child both think they own the value → make ownership **explicit via prop or context**
- **God components**: > 200 lines, > 5 unrelated props → **split by responsibility**

## Patterns to apply

### 1. Compound components

```tsx
<Tabs defaultValue="overview">
  <Tabs.List>
    <Tabs.Trigger value="overview">Overview</Tabs.Trigger>
    <Tabs.Trigger value="settings">Settings</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Content value="overview">...</Tabs.Content>
  <Tabs.Content value="settings">...</Tabs.Content>
</Tabs>
```

Implementation: parent holds state via context, children read it.

### 2. Variants via single prop + design tokens

```tsx
<Button variant="primary" size="md">  // not: isPrimary={true} isMedium={true}
```

Variant set is **closed and documented** — easier to maintain than boolean combinations.

### 3. Explicit slot props

```tsx
<Card
  header={<Avatar />}
  body={<Description />}
  footer={<Actions />}
/>
```

Better than `<Card hasAvatar={true} title="..." description="..." actions={[...]}/>`.

### 4. Headless + styled split

Build behavior (state, ARIA, keyboard) separately from style. Lets consumers restyle without forking.

## Workflow when refactoring

1. List all props of the component
2. Group props into: **identity**, **content**, **variants**, **callbacks**, **internal state escape hatches**
3. Eliminate booleans: convert N boolean flags into 1 variant enum
4. Move content props (header/body/footer-like) into subcomponents
5. Move internal-state escape hatches behind an `unstyled` or `headless` variant
6. Confirm: every public prop is a noun (`size`), not a state question (`isOpen`)

## When NOT to over-compose

- A truly simple primitive (e.g., `<Spinner />`) needs no slots
- One-off internal components don't need a public API
- < 3 instances of the component in the codebase → don't pre-abstract
