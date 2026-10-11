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
          950: '#080808',
          900: '#0F0F0F',
          850: '#141414',
          800: '#181818',
          700: '#242424',
          600: '#333333',
        },
        brand: {
          red: '#B3121B',
          'red-bright': '#D81924',
          'red-dark': '#850B12',
          gold: '#E5B842',
          silver: '#C0C0C0',
          bronze: '#CD7F32',
        },
        editorial: {
          white: '#F5F5F5',
          muted: '#9A9A9A',
          subtle: '#666666',
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
        'glow-red': '0 0 25px rgba(179, 18, 27, 0.45)',
        'glow-red-lg': '0 0 50px rgba(179, 18, 27, 0.3)',
      }
    },
  },
  plugins: [],
}
