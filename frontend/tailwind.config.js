/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0f4ff',
          100: '#dde7ff',
          200: '#c3d4ff',
          300: '#9db7ff',
          400: '#748eff',
          500: '#5265f5',
          600: '#3d47e8',
          700: '#3237ce',
          800: '#2b2fa7',
          900: '#292e84',
        },
        surface: {
          900: '#f0f4ff',
          800: '#ffffff',
          700: '#f1f5f9',
          600: '#e2e8f0',
          500: '#cbd5e1',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #5265f5, 0 0 10px #5265f5' },
          '100%': { boxShadow: '0 0 20px #748eff, 0 0 40px #748eff' },
        },
      },
    },
  },
  plugins: [],
}
