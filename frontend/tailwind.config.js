/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace']
      },
      colors: {
        primary: { DEFAULT: '#1E3A8A', 600: '#1D4ED8', 50: '#DBEAFE', 950: '#0F172A' },
        secondary: { DEFAULT: '#4338CA', 700: '#4A3B8C', 50: '#EDE9FE', 900: '#312E81' },
        emerald: { 500: '#10B981', 600: '#059669' },
        coral: { 500: '#F87171', 600: '#EF4444' },
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        'surface-alt': 'rgb(var(--color-surface-alt) / <alpha-value>)',
        bg: 'rgb(var(--color-bg) / <alpha-value>)',
        'text-primary': 'rgb(var(--color-text-primary) / <alpha-value>)',
        'text-secondary': 'rgb(var(--color-text-secondary) / <alpha-value>)',
        'text-muted': 'rgb(var(--color-text-muted) / <alpha-value>)',
        border: 'rgb(var(--color-border) / <alpha-value>)',
        'border-strong': 'rgb(var(--color-border-strong) / <alpha-value>)',
        accent: 'rgb(var(--color-accent) / <alpha-value>)',
        'accent-hover': 'rgb(var(--color-accent-hover) / <alpha-value>)',
        'accent-soft': 'rgb(var(--color-accent-soft) / <alpha-value>)',
        success: 'rgb(var(--color-success) / <alpha-value>)',
        danger: 'rgb(var(--color-danger) / <alpha-value>)',
        warning: 'rgb(var(--color-warning) / <alpha-value>)',
        info: 'rgb(var(--color-info) / <alpha-value>)',
        retiro: 'rgb(var(--color-retiro) / <alpha-value>)',
        distribucion: 'rgb(var(--color-distribucion) / <alpha-value>)',
      },
      boxShadow: {
        elevated: '0 10px 30px -12px rgba(59,130,246,0.20)'
      },
      fontFeatureSettings: {
        'tnum': '"tnum" 1',
        'lnum': '"lnum" 1'
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
