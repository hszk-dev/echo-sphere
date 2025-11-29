# EchoSphere Frontend Design System

**Version**: 1.0.0
**Date**: 2024-11-30
**Status**: Approved

---

## 1. Design Philosophy

### 1.1 Core Concept: "Ethereal Audio Space"

EchoSphere is a **voice-first** platform, not a video conferencing tool. The design philosophy centers on creating an immersive audio experience where sound becomes visible and tangible.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│     "Step into a space where your voice creates ripples,        │
│      and AI responds like an echo in a spherical chamber."      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Brand Essence

| Element | Meaning | Visual Expression |
|---------|---------|-------------------|
| **Echo** | Sound reflection, resonance | Wave patterns, ripple animations |
| **Sphere** | Immersive container, completeness | Circular forms, orb visualizers |

### 1.3 Design Principles

1. **Voice as Hero**: Audio visualization is the central UI element, not video thumbnails
2. **Calm Immersion**: Dark, ambient backgrounds that reduce visual fatigue during extended conversations
3. **Responsive Feedback**: Every interaction has immediate, satisfying visual/audio feedback
4. **Accessible by Default**: WCAG 2.1 AA compliance, keyboard navigation, screen reader support
5. **Progressive Disclosure**: Show essential controls first, reveal advanced options on demand

### 1.4 Comparison: Video vs Voice First Design

| Aspect | Video-First (Meet) | Voice-First (EchoSphere) |
|--------|-------------------|--------------------------|
| Central Element | Video grid | Audio visualizer |
| Visual Density | High (many faces) | Low (focused attention) |
| Color Palette | Bright, corporate | Dark, ambient |
| Animation | Minimal (bandwidth) | Rich (express audio states) |
| Screen Real Estate | Maximize video | Maximize breathing room |

---

## 2. Visual Identity

### 2.1 Color System

#### Primary Palette

```css
:root {
  /* Base: Deep space for immersive audio experience */
  --color-base-900: #0A0D12;   /* Deepest background */
  --color-base-800: #0F1419;   /* Primary background */
  --color-base-700: #1A1F26;   /* Elevated surfaces */
  --color-base-600: #242B35;   /* Cards, modals */
  --color-base-500: #2F3844;   /* Borders, dividers */
  --color-base-400: #4A5568;   /* Muted text */
  --color-base-300: #718096;   /* Secondary text */
  --color-base-200: #A0AEC0;   /* Primary text (muted) */
  --color-base-100: #E2E8F0;   /* Primary text */
  --color-base-50:  #F7FAFC;   /* Bright text, headings */

  /* Primary: Warm Coral — Voice energy, human warmth */
  --color-primary-50:  #FFF5F2;
  --color-primary-100: #FFE4DC;
  --color-primary-200: #FFCAB8;
  --color-primary-300: #FFA98E;
  --color-primary-400: #FF8264;
  --color-primary-500: #FF6B4A;  /* Primary accent */
  --color-primary-600: #E5523A;
  --color-primary-700: #BF3D2A;
  --color-primary-800: #99301F;
  --color-primary-900: #732415;

  /* Secondary: Soft Cyan — Digital precision, AI presence */
  --color-secondary-50:  #E6FFFA;
  --color-secondary-100: #B2F5EA;
  --color-secondary-200: #81E6D9;
  --color-secondary-300: #4FD1C5;
  --color-secondary-400: #38B2AC;
  --color-secondary-500: #319795;  /* Secondary accent */
  --color-secondary-600: #2C7A7B;
  --color-secondary-700: #285E61;
  --color-secondary-800: #234E52;
  --color-secondary-900: #1D4044;

  /* Semantic Colors */
  --color-success: #48BB78;
  --color-warning: #ECC94B;
  --color-error:   #F56565;
  --color-info:    #4299E1;

  /* Special: Audio Visualization Gradient */
  --gradient-voice: linear-gradient(135deg, #FF6B4A 0%, #FFA94D 50%, #4ECDC4 100%);
  --gradient-ai:    linear-gradient(135deg, #4ECDC4 0%, #6B8DD6 50%, #8E54E9 100%);
}
```

#### Dark Mode (Default)

EchoSphere defaults to dark mode for immersive audio experience.

```css
[data-theme="dark"] {
  --bg-primary:    var(--color-base-800);
  --bg-secondary:  var(--color-base-700);
  --bg-elevated:   var(--color-base-600);
  --text-primary:  var(--color-base-50);
  --text-secondary: var(--color-base-300);
  --text-muted:    var(--color-base-400);
  --border:        var(--color-base-500);
}
```

#### Light Mode

Light mode is fully supported for users who prefer a brighter interface.

```css
[data-theme="light"] {
  /* Backgrounds */
  --bg-primary:    #FFFFFF;
  --bg-secondary:  #F7FAFC;
  --bg-elevated:   #FFFFFF;
  --bg-muted:      #EDF2F7;

  /* Text */
  --text-primary:   var(--color-base-800);
  --text-secondary: var(--color-base-600);
  --text-muted:     var(--color-base-400);

  /* Borders & Dividers */
  --border:         #E2E8F0;
  --border-strong:  #CBD5E0;

  /* Shadows (lighter for light mode) */
  --shadow-sm:  0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md:  0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
  --shadow-lg:  0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.05);

  /* Glow effects (subtler for light mode) */
  --glow-primary:   0 0 20px rgba(255, 107, 74, 0.15);
  --glow-secondary: 0 0 20px rgba(49, 151, 149, 0.15);
}
```

#### Theme Switching

Implement theme switching using a data attribute on the root element:

```tsx
// Theme toggle example
function toggleTheme() {
  const html = document.documentElement;
  const currentTheme = html.dataset.theme;
  html.dataset.theme = currentTheme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', html.dataset.theme);
}

// Initialize theme from localStorage or system preference
function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.dataset.theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
}
```

### 2.2 Typography

#### Font Stack

| Role | Font Family | Weight | Fallback |
|------|-------------|--------|----------|
| **Display** | Cabinet Grotesk | 700, 800 | system-ui |
| **Heading** | Plus Jakarta Sans | 600, 700 | sans-serif |
| **Body** | Plus Jakarta Sans | 400, 500 | sans-serif |
| **Mono** | JetBrains Mono | 400 | monospace |

#### Font Loading (Self-Hosted)

Cabinet Grotesk is self-hosted from Fontshare for distinctive typography.

**Step 1: Download Fonts**

1. Visit [Fontshare - Cabinet Grotesk](https://www.fontshare.com/fonts/cabinet-grotesk)
2. Download the font family (Web format)
3. Extract and copy these files to `apps/web/src/fonts/`:
   - `CabinetGrotesk-Bold.woff2`
   - `CabinetGrotesk-Extrabold.woff2`

**Step 2: Configure Next.js Fonts**

```tsx
// apps/web/src/app/layout.tsx
import { Plus_Jakarta_Sans, JetBrains_Mono } from 'next/font/google';
import localFont from 'next/font/local';

// Self-hosted: Cabinet Grotesk (Display font)
const cabinetGrotesk = localFont({
  src: [
    { path: '../fonts/CabinetGrotesk-Bold.woff2', weight: '700', style: 'normal' },
    { path: '../fonts/CabinetGrotesk-Extrabold.woff2', weight: '800', style: 'normal' },
  ],
  variable: '--font-display',
  display: 'swap',
  preload: true,
});

// Google Fonts: Plus Jakarta Sans (Body font)
const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-body',
  display: 'swap',
});

// Google Fonts: JetBrains Mono (Code font)
const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400'],
  variable: '--font-mono',
  display: 'swap',
});

// Apply to html element
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      data-theme="dark"
      className={`${cabinetGrotesk.variable} ${plusJakarta.variable} ${jetbrainsMono.variable}`}
    >
      <body className="font-body bg-bg-primary text-text-primary">
        {children}
      </body>
    </html>
  );
}
```

**Directory Structure:**

```
apps/web/src/
├── fonts/
│   ├── CabinetGrotesk-Bold.woff2
│   └── CabinetGrotesk-Extrabold.woff2
└── app/
    └── layout.tsx
```

#### Type Scale

```css
:root {
  --text-xs:   0.75rem;    /* 12px */
  --text-sm:   0.875rem;   /* 14px */
  --text-base: 1rem;       /* 16px */
  --text-lg:   1.125rem;   /* 18px */
  --text-xl:   1.25rem;    /* 20px */
  --text-2xl:  1.5rem;     /* 24px */
  --text-3xl:  1.875rem;   /* 30px */
  --text-4xl:  2.25rem;    /* 36px */
  --text-5xl:  3rem;       /* 48px */
  --text-6xl:  3.75rem;    /* 60px */

  --leading-tight:  1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
}
```

### 2.3 Spacing & Layout

#### Spacing Scale

```css
:root {
  --space-0:  0;
  --space-1:  0.25rem;   /* 4px */
  --space-2:  0.5rem;    /* 8px */
  --space-3:  0.75rem;   /* 12px */
  --space-4:  1rem;      /* 16px */
  --space-5:  1.25rem;   /* 20px */
  --space-6:  1.5rem;    /* 24px */
  --space-8:  2rem;      /* 32px */
  --space-10: 2.5rem;    /* 40px */
  --space-12: 3rem;      /* 48px */
  --space-16: 4rem;      /* 64px */
  --space-20: 5rem;      /* 80px */
  --space-24: 6rem;      /* 96px */
}
```

#### Border Radius

```css
:root {
  --radius-sm:   0.375rem;  /* 6px - Small buttons, inputs */
  --radius-md:   0.5rem;    /* 8px - Cards */
  --radius-lg:   0.75rem;   /* 12px - Modals */
  --radius-xl:   1rem;      /* 16px - Large cards */
  --radius-2xl:  1.5rem;    /* 24px - Feature sections */
  --radius-full: 9999px;    /* Circular elements */
}
```

### 2.4 Shadows & Elevation

```css
:root {
  /* Soft shadows for dark mode */
  --shadow-sm:  0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md:  0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.3);
  --shadow-lg:  0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -4px rgba(0, 0, 0, 0.4);
  --shadow-xl:  0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.4);

  /* Glow effects for interactive elements */
  --glow-primary:   0 0 20px rgba(255, 107, 74, 0.3);
  --glow-secondary: 0 0 20px rgba(78, 205, 196, 0.3);
  --glow-error:     0 0 20px rgba(245, 101, 101, 0.3);
}
```

---

## 3. Motion & Animation

### 3.1 Animation Tokens

```css
:root {
  /* Duration */
  --duration-instant: 50ms;
  --duration-fast:    150ms;
  --duration-normal:  250ms;
  --duration-slow:    400ms;
  --duration-slower:  600ms;

  /* Easing */
  --ease-default:    cubic-bezier(0.4, 0, 0.2, 1);
  --ease-in:         cubic-bezier(0.4, 0, 1, 1);
  --ease-out:        cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out:     cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce:     cubic-bezier(0.68, -0.55, 0.265, 1.55);
  --ease-spring:     cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
```

### 3.2 Core Animations

#### Voice Pulse (AI Speaking)

```css
@keyframes voicePulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.08);
    opacity: 0.85;
  }
}

.voice-pulse {
  animation: voicePulse 1.5s var(--ease-in-out) infinite;
}
```

#### Audio Wave

```css
@keyframes audioWave {
  0%, 100% {
    transform: scaleY(0.3);
  }
  50% {
    transform: scaleY(1);
  }
}

.audio-bar {
  animation: audioWave 0.8s var(--ease-in-out) infinite;
}

.audio-bar:nth-child(1) { animation-delay: 0ms; }
.audio-bar:nth-child(2) { animation-delay: 100ms; }
.audio-bar:nth-child(3) { animation-delay: 200ms; }
.audio-bar:nth-child(4) { animation-delay: 300ms; }
.audio-bar:nth-child(5) { animation-delay: 400ms; }
```

#### Ripple Effect (Voice Sent)

```css
@keyframes ripple {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
}

.ripple {
  animation: ripple 1s var(--ease-out) forwards;
}
```

#### Thinking State (AI Processing)

```css
@keyframes thinking {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 200% 50%;
  }
}

.thinking-indicator {
  background: linear-gradient(
    90deg,
    var(--color-secondary-500) 0%,
    var(--color-secondary-300) 25%,
    var(--color-secondary-500) 50%,
    var(--color-secondary-300) 75%,
    var(--color-secondary-500) 100%
  );
  background-size: 200% 100%;
  animation: thinking 2s linear infinite;
}
```

### 3.3 Motion Principles

1. **Audio-Reactive**: Visualizations respond to actual audio levels
2. **State-Driven**: Animation clearly indicates AI state (listening, thinking, speaking)
3. **Performance-First**: Prefer CSS animations over JS for smooth 60fps
4. **Reduced Motion**: Respect `prefers-reduced-motion` media query

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 4. Component Library

### 4.1 Component Architecture

```
src/
├── shared/
│   └── components/
│       └── ui/              # Base primitives (shadcn/ui)
│           ├── button.tsx
│           ├── card.tsx
│           ├── input.tsx
│           └── ...
└── features/
    └── voice-room/
        └── components/      # Feature-specific components
            ├── VoiceRoom.tsx
            ├── AudioOrb.tsx
            ├── AudioVisualizer.tsx
            ├── ControlBar.tsx
            ├── TranscriptPanel.tsx
            └── DeviceSelector.tsx
```

### 4.2 Core Components

#### Button Variants

| Variant | Use Case | Visual |
|---------|----------|--------|
| `primary` | Main CTA ("Start Session") | Coral gradient, glow on hover |
| `secondary` | Secondary actions | Cyan outline |
| `ghost` | Tertiary actions | Transparent, text only |
| `danger` | Destructive ("End Session") | Red, isolated |
| `icon` | Icon-only buttons | Circular, subtle background |

```tsx
// Button component example
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger' | 'icon';
  size: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  children: React.ReactNode;
}
```

#### Audio Orb (Central Visualizer)

The Audio Orb is the hero element of the voice room. It represents the AI's presence and state.

```tsx
interface AudioOrbProps {
  state: 'idle' | 'listening' | 'thinking' | 'speaking';
  audioLevel?: number;  // 0-1, for reactive sizing
  size?: 'sm' | 'md' | 'lg';
}
```

| State | Visual | Animation |
|-------|--------|-----------|
| `idle` | Soft cyan glow | Gentle breathing pulse |
| `listening` | Coral rim, expanding | Reactive to user voice |
| `thinking` | Gradient sweep | Shimmer animation |
| `speaking` | Pulsing coral core | Sync with audio output |

#### Control Bar

```tsx
interface ControlBarProps {
  controls: {
    microphone: boolean;
    speaker: boolean;
    settings: boolean;
    leave: boolean;
  };
  position: 'bottom' | 'floating';
  autoHide?: boolean;  // Hide when inactive
}
```

#### Transcript Panel

```tsx
interface TranscriptPanelProps {
  messages: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
  }>;
  isOpen: boolean;
  onToggle: () => void;
}
```

### 4.3 Component States

Every interactive component should handle these states:

| State | Description | Visual Feedback |
|-------|-------------|-----------------|
| `default` | Normal state | Base styling |
| `hover` | Mouse over | Subtle lift, glow |
| `focus` | Keyboard focus | Visible ring |
| `active` | Being pressed | Scale down slightly |
| `disabled` | Not interactive | Reduced opacity |
| `loading` | Async operation | Spinner, skeleton |
| `error` | Error state | Red border, message |

---

## 5. Screen Specifications

### 5.1 Home Screen

**Purpose**: Entry point. Users choose to start a new session or join an existing one.

**Layout**: Two-column split (60/40) on desktop, single column on mobile.

```
┌─────────────────────────────────────────────────────────────────┐
│  [Logo]                                      [Time] [Settings]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────┐  ┌─────────────────────────┐  │
│   │                             │  │                         │  │
│   │    "Start a Voice          │  │   [Animated Orb         │  │
│   │     Conversation"          │  │    Preview]             │  │
│   │                             │  │                         │  │
│   │    [New Session Button]    │  │                         │  │
│   │                             │  │   "Experience AI        │  │
│   │    ────── or ──────        │  │    that listens."       │  │
│   │                             │  │                         │  │
│   │    [Room Code Input]       │  │                         │  │
│   │    [Join Button]           │  │                         │  │
│   │                             │  │                         │  │
│   └─────────────────────────────┘  └─────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Elements**:
- **Primary CTA**: "New Session" button with coral gradient
- **Secondary CTA**: Room code input with "Join" button
- **Hero Visual**: Animated Audio Orb preview (attracts attention)
- **Microcopy**: Brief tagline about the experience

**Interactions**:
- New Session button generates UUID room name and navigates
- Join button validates room code format before navigation
- Orb preview animates on page load (staggered reveal)

### 5.2 Pre-Join Screen (Green Room)

**Purpose**: Device check before entering the voice room. Build confidence.

**Layout**: Centered single column with device preview.

```
┌─────────────────────────────────────────────────────────────────┐
│                            [Back]                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌─────────────────────────┐                   │
│                    │                         │                   │
│                    │   [Audio Level Meter]   │                   │
│                    │                         │                   │
│                    │   ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁       │                   │
│                    │                         │                   │
│                    │   "Your microphone      │                   │
│                    │    is working"          │                   │
│                    │                         │                   │
│                    └─────────────────────────┘                   │
│                                                                  │
│                    [Microphone Dropdown  ▼]                      │
│                    [Speaker Dropdown     ▼]                      │
│                                                                  │
│                    ┌─────────────────────────┐                   │
│                    │    Join Session         │                   │
│                    └─────────────────────────┘                   │
│                                                                  │
│                    "Agent: エコスフィア"                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Elements**:
- **Audio Level Visualizer**: Real-time mic input feedback
- **Device Selectors**: Dropdowns for mic/speaker selection
- **Status Message**: Clear indication of device health
- **Join Button**: Large, prominent CTA

**Interactions**:
- Audio visualizer reacts to microphone input in real-time
- Device dropdowns refresh on device change events
- "Test Speaker" button plays sample audio
- Join button disabled until microphone permission granted

### 5.3 Voice Room (Meeting Screen)

**Purpose**: The main interaction space. Focus on the conversation.

**Layout**: Full-screen with Audio Orb as central element.

```
┌─────────────────────────────────────────────────────────────────┐
│  [Status: Connected]              [Session Time]   [Transcript] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                                                                  │
│                                                                  │
│                         ╭─────────╮                              │
│                       ╱             ╲                            │
│                      │   [Audio     │                            │
│                      │    Orb]      │                            │
│                       ╲             ╱                            │
│                         ╰─────────╯                              │
│                                                                  │
│                       "Listening..."                             │
│                                                                  │
│                                                                  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│              [Mute]    [Settings]    [End Session]              │
└─────────────────────────────────────────────────────────────────┘
```

**Key Elements**:
- **Audio Orb**: Large, centered, state-driven visualization
- **State Label**: Text below orb ("Listening", "Thinking", "Speaking")
- **Control Bar**: Minimal controls at bottom
- **Transcript Panel**: Slide-in panel from right edge (optional)
- **Session Timer**: Subtle timer in header

**Interactions**:
- Orb animation syncs with AI state from `useVoiceAssistant` hook
- Control bar auto-hides after 3 seconds of inactivity
- Transcript panel toggles via button or keyboard shortcut (T)
- End Session button requires confirmation

**State Transitions**:
```
idle → listening (user speaks)
listening → thinking (speech ends)
thinking → speaking (AI responds)
speaking → listening (AI finishes)
```

### 5.4 Transcript Panel (Overlay)

**Purpose**: Show conversation history without leaving the room.

**Layout**: Right-side slide-in panel.

```
┌───────────────────────────────────────────────────────────────────────┐
│                                          │ Transcript                 │
│                                          │ ──────────────────────────│
│                                          │                            │
│          [Voice Room Content]            │ 🙂 こんにちは              │
│                                          │    15:23                   │
│                                          │                            │
│                                          │ 🤖 こんにちは！エコスフィア │
│                                          │    です。何かお手伝いでき   │
│                                          │    ることはありますか？    │
│                                          │    15:23                   │
│                                          │                            │
│                                          │ 🙂 今日の天気は？          │
│                                          │    15:24                   │
│                                          │                            │
│                                          │ 🤖 ...                     │
│                                          │                            │
└───────────────────────────────────────────────────────────────────────┘
```

**Key Elements**:
- **Message Bubbles**: Distinct styling for user vs AI
- **Timestamps**: Relative time (just now, 1 min ago)
- **Auto-scroll**: New messages scroll into view
- **Close Button**: X button or swipe gesture

---

## 6. Accessibility

### 6.1 Requirements

- **WCAG 2.1 Level AA** compliance
- **Keyboard Navigation**: All interactions accessible via keyboard
- **Screen Reader**: Proper ARIA labels and live regions
- **Color Contrast**: Minimum 4.5:1 for text, 3:1 for UI components

### 6.2 Voice Room Accessibility

```tsx
// Example: Audio Orb with accessibility
<div
  role="status"
  aria-live="polite"
  aria-label={`AI is currently ${state}`}
>
  <AudioOrb state={state} />
  <span className="sr-only">
    {state === 'listening' && 'AI is listening to you'}
    {state === 'thinking' && 'AI is processing your request'}
    {state === 'speaking' && 'AI is speaking'}
  </span>
</div>
```

### 6.3 Focus Management

```css
/* Visible focus ring for keyboard users */
:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}

/* Hide focus ring for mouse users */
:focus:not(:focus-visible) {
  outline: none;
}
```

---

## 7. Responsive Design

### 7.1 Breakpoints

```css
:root {
  --breakpoint-sm:  640px;   /* Mobile landscape */
  --breakpoint-md:  768px;   /* Tablet portrait */
  --breakpoint-lg:  1024px;  /* Tablet landscape / Small desktop */
  --breakpoint-xl:  1280px;  /* Desktop */
  --breakpoint-2xl: 1536px;  /* Large desktop */
}
```

### 7.2 Layout Adaptations

| Screen | Home | Pre-Join | Voice Room |
|--------|------|----------|------------|
| Mobile | Single column, stacked | Full width | Orb 80% width, controls always visible |
| Tablet | Two columns | Centered card | Orb 60% width, controls visible |
| Desktop | Two columns (60/40) | Centered card | Orb 40% width, auto-hide controls |

### 7.3 Touch Considerations

- Minimum touch target: 44x44px
- Increased spacing between controls on mobile
- Swipe gestures for transcript panel
- Long-press for secondary actions

---

## 8. Implementation Guidelines

### 8.1 CSS Architecture

Use Tailwind CSS with custom design tokens:

```js
// tailwind.config.ts
module.exports = {
  theme: {
    extend: {
      colors: {
        base: {
          900: '#0A0D12',
          800: '#0F1419',
          // ... etc
        },
        primary: {
          500: '#FF6B4A',
          // ... etc
        },
        secondary: {
          500: '#319795',
          // ... etc
        },
      },
      fontFamily: {
        display: ['var(--font-display)', 'system-ui'],
        body: ['var(--font-body)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      animation: {
        'voice-pulse': 'voicePulse 1.5s ease-in-out infinite',
        'audio-wave': 'audioWave 0.8s ease-in-out infinite',
        'ripple': 'ripple 1s ease-out forwards',
      },
    },
  },
};
```

### 8.2 Component Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Feature Component | PascalCase | `VoiceRoom.tsx` |
| UI Primitive | PascalCase | `Button.tsx` |
| Hook | camelCase with `use` prefix | `useVoiceSession.ts` |
| Utility | camelCase | `formatDuration.ts` |
| Constant | SCREAMING_SNAKE_CASE | `MAX_SESSION_DURATION` |

### 8.3 File Co-location

```
features/
└── voice-room/
    ├── components/
    │   ├── VoiceRoom.tsx
    │   ├── VoiceRoom.test.tsx    # Co-located tests
    │   └── VoiceRoom.stories.tsx # Co-located stories (optional)
    ├── hooks/
    │   └── useVoiceSession.ts
    ├── types/
    │   └── index.ts
    └── index.ts                   # Public exports
```

---

## 9. Design Tokens Summary

### Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════╗
║                    ECHOSPHERE DESIGN TOKENS                       ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  COLORS                                                            ║
║  ───────────────────────────────────────────────────────────────  ║
║  Background:  #0F1419 (base-800)                                   ║
║  Surface:     #1A1F26 (base-700)                                   ║
║  Primary:     #FF6B4A (coral)                                      ║
║  Secondary:   #319795 (cyan)                                       ║
║  Text:        #F7FAFC (base-50)                                    ║
║                                                                    ║
║  TYPOGRAPHY                                                        ║
║  ───────────────────────────────────────────────────────────────  ║
║  Display:     Cabinet Grotesk Bold                                 ║
║  Body:        Plus Jakarta Sans Regular                            ║
║  Mono:        JetBrains Mono                                       ║
║                                                                    ║
║  SPACING                                                           ║
║  ───────────────────────────────────────────────────────────────  ║
║  Base unit:   4px (--space-1)                                      ║
║  Component:   16px (--space-4)                                     ║
║  Section:     48px (--space-12)                                    ║
║                                                                    ║
║  ANIMATION                                                         ║
║  ───────────────────────────────────────────────────────────────  ║
║  Duration:    250ms (normal)                                       ║
║  Easing:      cubic-bezier(0.4, 0, 0.2, 1)                        ║
║                                                                    ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 10. Next Steps

### Phase 1 Implementation Checklist

- [ ] Set up Tailwind CSS with custom design tokens
- [ ] Install and configure fonts (Cabinet Grotesk, Plus Jakarta Sans)
- [ ] Create base UI components (Button, Card, Input)
- [ ] Implement Audio Orb visualizer component
- [ ] Build Voice Room layout with Control Bar
- [ ] Add responsive breakpoints
- [ ] Test accessibility with screen reader
- [ ] Document component usage in Storybook (optional)

---

## Appendix A: Reference Images

See attached mockups for visual reference:
- Home Screen: [Figma Link TBD]
- Pre-Join: [Figma Link TBD]
- Voice Room: [Figma Link TBD]

## Appendix B: Design Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-11-30 | Dark mode default | Immersive audio experience, reduce eye strain |
| 2024-11-30 | Light mode support | User preference, accessibility in bright environments |
| 2024-11-30 | Coral primary color | Warmth, human voice energy, contrast with cyan AI |
| 2024-11-30 | Audio Orb as hero | Voice-first design, not video grid |
| 2024-11-30 | Cabinet Grotesk font (self-hosted) | Distinctive, modern, avoids generic AI aesthetic, not available on Google Fonts |
| 2024-11-30 | Plus Jakarta Sans body font | Clean, readable, slightly warm, Google Fonts for easy loading |
| 2024-11-30 | Avatar deferred to Phase 3 | Focus on core voice interaction first |
