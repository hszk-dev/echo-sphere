import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#FF6B4A",
          50: "#FFF0ED",
          100: "#FFE1DB",
          200: "#FFC3B7",
          300: "#FFA593",
          400: "#FF876F",
          500: "#FF6B4A",
          600: "#FF3D14",
          700: "#DD2600",
          800: "#A61C00",
          900: "#6E1300",
        },
        secondary: {
          DEFAULT: "#319795",
          light: "#319795",
          dark: "#2C7A7B",
          50: "#E6FFFA",
          100: "#B2F5EA",
          200: "#81E6D9",
          300: "#4FD1C5",
          400: "#38B2AC",
          500: "#319795",
          600: "#2C7A7B",
          700: "#285E61",
          800: "#234E52",
          900: "#1D4044",
        },
        background: {
          DEFAULT: "var(--background)",
          dark: "#0D0D0D",
          light: "#FAFAFA",
        },
        surface: {
          DEFAULT: "var(--surface)",
          dark: "#1A1A1A",
          light: "#FFFFFF",
        },
        foreground: {
          DEFAULT: "var(--foreground)",
          dark: "#FFFFFF",
          light: "#1A1A1A",
        },
        muted: {
          DEFAULT: "var(--muted)",
          dark: "#A1A1A1",
          light: "#6B7280",
        },
        border: {
          DEFAULT: "var(--border)",
          dark: "#2D2D2D",
          light: "#E5E7EB",
        },
      },
      fontFamily: {
        display: ["var(--font-cabinet)", "system-ui", "sans-serif"],
        sans: ["var(--font-jakarta)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "ui-monospace", "monospace"],
      },
      fontSize: {
        "display-xl": ["4.5rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-lg": ["3.75rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-md": ["3rem", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
        "display-sm": ["2.25rem", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "fade-out": "fadeOut 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "slide-down": "slideDown 0.3s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
        "spin-slow": "spin 3s linear infinite",
        ripple: "ripple 1.5s ease-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeOut: {
          "0%": { opacity: "1" },
          "100%": { opacity: "0" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        ripple: {
          "0%": { transform: "scale(1)", opacity: "0.4" },
          "100%": { transform: "scale(2.5)", opacity: "0" },
        },
      },
      borderRadius: {
        "4xl": "2rem",
      },
      boxShadow: {
        glow: "0 0 20px rgba(255, 107, 74, 0.3)",
        "glow-lg": "0 0 40px rgba(255, 107, 74, 0.4)",
      },
    },
  },
  plugins: [],
};

export default config;
