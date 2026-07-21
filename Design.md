# DigiSutra Minimal Creator System Design

Inspired by: Linear, Vercel, Raycast, Notion, Stripe

## Overview

Minimal Creator is a premium workspace for creators and customers. Users browse, purchase, manage, and consume digital products in a calm, distraction-free environment.

The interface should feel intentional, fast, and trustworthy. Every screen should emphasize the content, not the interface.

The design direction is Quiet Professionalism: neutral surfaces, precise spacing, strong typography, restrained motion, and purposeful color.

The product should feel closer to Stripe Dashboard than Dribbble.

## Design Philosophy

### Content First

- Digital products are the hero.
- UI exists to support discovery, purchase, and consumption.

### Minimal by Default

- Every element must justify its existence.
- If removing something improves clarity, remove it.

### Calm Interfaces

- No unnecessary decoration.
- No gradients for decoration.
- No oversized illustrations inside the application.
- No floating glass panels.

### Speed Feels Premium

- Interfaces should appear instantly.
- Loading states should preserve layout.
- Animations should never slow navigation.

### Consistency Over Creativity

- Buttons always behave the same.
- Cards always behave the same.
- Forms always behave the same.
- Users should never need to learn the interface twice.

## Visual Personality

The application should feel like:

- Linear
- Vercel
- Stripe
- Notion
- Raycast

## Keywords

- Minimal
- Professional
- Editorial
- Quiet
- Modern
- Technical
- Premium
- Confident
- Focused

## Avoid

- Playful
- Cartoon
- Neumorphism
- Heavy glassmorphism
- Material Design 2
- Bright gradients
- Gaming UI

## Visual Foundations

### Background

- Soft neutral gray.
- Never pure white.

### Surfaces

- Paper-like but modern.
- Very subtle elevation.
- Minimal borders.

### Borders

- Thin.
- Consistent.
- Used more often than shadows.

### Shadows

- Soft.
- Diffuse.
- Never dramatic.
- Elevation should communicate grouping, not decoration.

### Radius

- Small to medium.
- Consistent across the application.
- Avoid oversized pill shapes.

## Typography

### Primary

- Inter

### Alternative

- Geist

### Usage

- Large headings.
- Comfortable body text.
- Excellent line height.
- Financial values use tabular numbers.
- Product titles receive more emphasis than supporting metadata.

## Color Strategy

Use color intentionally.

### Primary Accent

- Blue

### Success

- Green

### Warning

- Amber

### Danger

- Red

### Neutral

- Gray

- Never introduce multiple competing accent colors on the same page.

## Layout

- Use whitespace generously.
- Maximum content width: 1280px.

### Dashboard

- Sidebar
- Content
- Optional contextual panel

- Avoid deeply nested layouts.

### Navigation

- Navigation should disappear mentally.
- Sidebar remains stable.
- Search is globally accessible.
- Breadcrumbs only when hierarchy becomes deep.

## Components

### Buttons

- Primary
- Secondary
- Ghost
- Destructive

- No more.

### Cards

- Cards group meaningful information.
- Never use cards simply because whitespace exists.

### Forms

- Always show labels.
- Validation appears below inputs.
- Required fields are explicit.

### Tables

- Compact.
- Readable.
- Keyboard accessible.
- Search before filters.
- Filters before sorting.

### Dialogs

- Reserved for destructive actions or focused workflows.
- Avoid modal-heavy experiences.

## Product Catalog

Products appear in clean grids.

Cards emphasize:

- Cover
- Title
- Creator
- Price
- Rating

Metadata remains secondary.

## Product Detail

Hierarchy:

- Cover
- Title
- Price
- Purchase CTA
- Description
- Preview
- FAQ
- Reviews

- Avoid visual clutter around the purchase button.

## Checkout

- One page.
- Minimal fields.
- Fast.
- Trust signals near payment.
- No distractions.

## Customer Library

Purchased products feel like a personal workspace.

Focus on:

- Continue reading
- Recent downloads
- Updates
- Search
- Collections

## Seller Dashboard

Sections:

- Overview
- Products
- Orders
- Customers
- Analytics
- Payouts
- Settings

- Analytics should emphasize trends rather than decorative charts.

## Motion

### Duration

- 180ms to 220ms

### Allowed

- Fade
- Scale
- Slide
- Opacity

### Avoid

- Bounce
- Elastic animations
- Parallax
- Long transitions

## Empty States

- Simple illustration.
- One sentence.
- One action.
- Never paragraphs.

## Loading

- Prefer skeletons.
- Never shift layout.
- Never block navigation unnecessarily.

## Accessibility

- WCAG AA.
- Visible keyboard focus.
- 44px touch targets.
- Never rely solely on color.

## Responsive

### Desktop

- Information dense.

### Tablet

- Reduce columns.

### Mobile

- Single column.
- Sticky primary actions.
- No horizontal scrolling.

## AI Design Instructions

When generating interfaces:

- Use shadcn/ui components.
- Use Tailwind CSS.
- Prefer composition over custom widgets.
- Reuse existing components before creating new ones.
- Maintain an 8px spacing system.
- Never introduce new colors without updating design tokens.
- Every page must have one obvious primary action.
- Avoid unnecessary visual complexity.
- Optimize for keyboard navigation and accessibility.

