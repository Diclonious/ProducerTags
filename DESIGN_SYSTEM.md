# TaggedByBelle Design System

## Overview

TaggedByBelle features a modern, clean design system inspired by industry-leading products like Notion, Linear, and Vercel. This document outlines the design principles, components, and implementation details.

---

## Design Principles

### 1. **Clarity & Simplicity**
- Clean layouts with generous whitespace
- Clear visual hierarchy
- Minimal cognitive load

### 2. **Consistency**
- Unified color palette across all pages
- Consistent spacing and typography
- Reusable component patterns

### 3. **Accessibility**
- WCAG 2.1 AA compliant
- Semantic HTML
- Keyboard navigation support
- Screen reader friendly

### 4. **Performance**
- Optimized CSS and JavaScript
- Fast load times
- Smooth animations (60fps)

---

## Color System

### Brand Colors
```css
--brand: #e2fb52          /* Electric Lime - Primary brand color */
--brand-hover: #d4ed4a    /* Hover state */
--brand-subtle: rgba(226, 251, 82, 0.1)  /* Backgrounds */
```

### Neutrals (Dark Theme)
```css
--bg-primary: #0a0e17     /* Main background */
--bg-secondary: #0e1422   /* Secondary surfaces */
--bg-tertiary: #151b2b    /* Tertiary surfaces */
--bg-elevated: #1a2235    /* Elevated elements */

--surface: #0e1422        /* Card backgrounds */
--surface-hover: #151b2b  /* Hover states */
--surface-active: #1a2235 /* Active states */
```

### Borders
```css
--border-subtle: rgba(255, 255, 255, 0.06)
--border-default: rgba(255, 255, 255, 0.1)
--border-strong: rgba(255, 255, 255, 0.18)
```

### Text
```css
--text-primary: #e6e9ef    /* Primary text */
--text-secondary: #9aa4b2  /* Secondary text */
--text-tertiary: #6b7280   /* Tertiary text */
--text-inverse: #0a0e17    /* Text on light backgrounds */
```

### Status Colors
```css
--status-active: #3b82f6   /* Blue - Active orders */
--status-delivered: #10b981 /* Green - Delivered */
--status-late: #ef4444     /* Red - Late orders */
--status-revision: #f59e0b /* Yellow - In revision */
--status-completed: #6b7280 /* Gray - Completed */
--status-cancelled: #dc2626 /* Red - Cancelled */
--status-dispute: #8b5cf6  /* Purple - In dispute */
```

---

## Typography

### Font Family
```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
```

### Font Sizes
```css
--text-xs: 0.75rem    /* 12px */
--text-sm: 0.875rem   /* 14px */
--text-base: 1rem     /* 16px */
--text-lg: 1.125rem   /* 18px */
--text-xl: 1.25rem    /* 20px */
--text-2xl: 1.5rem    /* 24px */
--text-3xl: 1.875rem  /* 30px */
--text-4xl: 2.25rem   /* 36px */
--text-5xl: 3rem      /* 48px */
```

### Font Weights
- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700
- Extrabold: 800
- Black: 900

---

## Spacing Scale

Based on a 4px base unit:
```css
--space-1: 0.25rem   /* 4px */
--space-2: 0.5rem    /* 8px */
--space-3: 0.75rem   /* 12px */
--space-4: 1rem      /* 16px */
--space-5: 1.25rem   /* 20px */
--space-6: 1.5rem    /* 24px */
--space-8: 2rem      /* 32px */
--space-10: 2.5rem   /* 40px */
--space-12: 3rem     /* 48px */
--space-16: 4rem     /* 64px */
--space-20: 5rem     /* 80px */
```

---

## Components

### Buttons

#### Primary Button
```html
<button class="btn btn-primary">
  Primary Action
</button>
```
- Background: `--brand`
- Use for primary actions (Create Order, Save Changes)
- Includes hover glow effect

#### Secondary Button
```html
<button class="btn btn-secondary">
  Secondary Action
</button>
```
- Background: `--surface`
- Border: `--border-default`
- Use for secondary actions (Cancel, View)

#### Ghost Button
```html
<button class="btn btn-ghost">
  Ghost Action
</button>
```
- Transparent background
- Use for tertiary actions

### Cards

```html
<div class="card">
  <!-- Card content -->
</div>
```
- Background: `--surface`
- Border: `--border-subtle`
- Border radius: `--radius-xl`
- Hover effect: Lift with shadow

### Badges

```html
<span class="badge badge-active">Active</span>
<span class="badge badge-delivered">Delivered</span>
<span class="badge badge-late">Late</span>
```

Status badges with consistent styling across the app.

### Forms

```html
<div class="form-group">
  <label class="form-label" for="input">Label</label>
  <input type="text" id="input" class="form-input" placeholder="Placeholder">
  <span class="form-help">Helper text</span>
</div>
```

---

## Animations

### Duration
```css
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1)
--transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1)
--transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1)
```

### Common Animations

#### Fade In
```css
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

#### Skeleton Loading
```css
.skeleton {
  animation: skeleton-loading 1.5s ease-in-out infinite;
}
```

---

## Layout Patterns

### Dashboard Layout
```html
<div class="dashboard-layout">
  <aside class="dashboard-sidebar">
    <!-- Sidebar content -->
  </aside>
  <main class="dashboard-main">
    <!-- Main content -->
  </main>
</div>
```

### Container
```html
<div class="container">
  <!-- Max-width constrained content -->
</div>
```

---

## Responsive Breakpoints

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

---

## Accessibility

### ARIA Labels
All interactive elements include appropriate ARIA labels and roles.

### Keyboard Navigation
- Tab order follows logical flow
- All actions accessible via keyboard
- Focus indicators visible

### Color Contrast
- All text meets WCAG AA standards
- Minimum 4.5:1 contrast for normal text
- Minimum 3:1 contrast for large text

---

## Best Practices

### Do's ✅
- Use design tokens (CSS variables) instead of hard-coded values
- Maintain consistent spacing throughout
- Use semantic HTML elements
- Add hover and focus states to interactive elements
- Test on multiple screen sizes

### Don'ts ❌
- Don't use inline styles
- Don't create custom colors outside the palette
- Don't forget loading and error states
- Don't skip accessibility attributes
- Don't use multiple animation timings

---

## File Structure

```
app/
├── static/
│   ├── css/
│   │   └── main.css          # Complete design system
│   ├── js/
│   │   └── main.js           # Interactive components
│   └── images/
├── templates/
│   ├── base.html             # Base template with navigation
│   ├── index.html            # Homepage
│   ├── login.html            # Authentication
│   ├── signup.html
│   ├── myorders.html         # User dashboard
│   ├── myorders-admin.html   # Admin dashboard
│   ├── profile.html          # Profile settings
│   └── analytics.html        # Analytics dashboard
└── core/
    └── config.py             # Application configuration
```

---

## Future Enhancements

- [ ] Dark/Light mode toggle
- [ ] Custom theme builder
- [ ] More animation options
- [ ] Component library expansion
- [ ] Design tokens JSON export

---

## Resources

- **Inter Font**: https://fonts.google.com/specimen/Inter
- **Chart.js**: https://www.chartjs.org/
- **CSS Variables Reference**: https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties

---

## Support

For questions or suggestions about the design system, please create an issue on the project repository.

**Version**: 2.0.0  
**Last Updated**: November 2025

