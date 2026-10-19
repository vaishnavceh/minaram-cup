/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pitch: {
          950: '#020617',
          900: '#030d26',
          850: '#06143c',
          800: '#0a1c52',
          700: '#0f296f',
          600: '#1d4ed8',
        },
        brand: {
          red: '#2563eb', // UCL Electric Blue replaces legacy red
          'red-bright': '#38bdf8', // UCL Electric Cyan
          'red-dark': '#1e40af', // Deep UCL Navy Blue
          gold: '#fbbf24', // Trophy Gold
          silver: '#e2e8f0', // Silver Starball Chrome
          bronze: '#d97706',
          ucl: '#2563eb',
          'ucl-cyan': '#00f0ff',
          'ucl-navy': '#020718',
          'ucl-deep': '#030d28',
        },
        editorial: {
          white: '#F5F5F5',
          muted: '#94a3b8',
          subtle: '#64748b',
        }
      },
      fontFamily: {
        display: ['"Bebas Neue"', 'Impact', 'sans-serif'],
        sans: ['"Inter"', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      letterSpacing: {
        widest: '.2em',
        tightest: '-.04em',
      },
      boxShadow: {
        'glow-red': '0 0 25px rgba(37, 99, 235, 0.55)',
        'glow-red-lg': '0 0 50px rgba(56, 189, 248, 0.45)',
        'glow-blue': '0 0 25px rgba(37, 99, 235, 0.55)',
        'glow-cyan': '0 0 25px rgba(6, 182, 212, 0.55)',
        'ucl-card': '0 8px 32px 0 rgba(2, 6, 23, 0.65)',
      }
    },
  },
  plugins: [],
}
