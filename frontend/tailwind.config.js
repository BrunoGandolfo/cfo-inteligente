/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#1E3A8A', 600: '#1D4ED8', 50: '#DBEAFE', 950: '#0F172A' },
        secondary: { DEFAULT: '#4338CA', 700: '#4A3B8C', 50: '#EDE9FE', 900: '#312E81' },
        emerald: { 500: '#10B981', 600: '#059669' },
        coral: { 500: '#F87171', 600: '#EF4444' }
      },
      boxShadow: {
        elevated: '0 10px 30px -12px rgba(59,130,246,0.20)'
      }
    },
  },
  plugins: [],
}
