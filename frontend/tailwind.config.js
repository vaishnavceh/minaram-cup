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
          950: '#020408',
          900: '#04060B',
          850: '#080C16',
          800: '#0F1626',
          750: '#162035',
          700: '#1e293b',
          600: '#334155',
        },
        tribute: {
          gold: '#D4AF37',
          'gold-light': '#FDE047',
          'gold-dark': '#A16207',
          crimson: '#E11D48',
          'crimson-bright': '#FB7185',
          'crimson-dark': '#9F1239',
          sky: '#38BDF8',
          'sky-bright': '#7DD3FC',
          'sky-dark': '#0284C7',
          canary: '#EAB308',
          'canary-bright': '#FDE047',
          emerald: '#10B981',
          'emerald-dark': '#047857',
        },
        brand: {
          red: '#E11D48', // Genuine Quinas Crimson Red
          'red-bright': '#FB7185',
          'red-dark': '#9F1239',
          gold: '#D4AF37', // Championship Trophy Gold
          'gold-light': '#FDE047',
          silver: '#E2E8F0', // Platinum Chrome
          bronze: '#CD7F32',
        },
        editorial: {
          white: '#FFFFFF',
          cream: '#F8FAFC',
          silver: '#CBD5E1',
          muted: '#94A3B8',
          subtle: '#64748B',
          dark: '#334155',
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
        'glow-red': '0 0 25px rgba(225, 29, 72, 0.45)',
        'glow-crimson': '0 0 25px rgba(225, 29, 72, 0.45)',
        'glow-gold': '0 0 25px rgba(212, 175, 55, 0.45)',
        'glow-gold-lg': '0 0 50px rgba(212, 175, 55, 0.35)',
        'glow-sky': '0 0 25px rgba(56, 189, 248, 0.45)',
        'glow-emerald': '0 0 25px rgba(16, 185, 129, 0.45)',
        'tribute-card': '0 12px 36px -4px rgba(0, 0, 0, 0.8)',
      }
    },
  },
  plugins: [],
}
