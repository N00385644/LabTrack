/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f1f5fb',
          100: '#dce6f5',
          200: '#bccfe9',
          300: '#8fadd8',
          400: '#5b82c1',
          500: '#3a63a8',
          600: '#2a4d8c',
          700: '#233f72',
          800: '#1d345d',
          900: '#0b1f3a',
          950: '#071628',
        },
        teal: {
          50: '#effcf9',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
      },
      fontFamily: {
        sans: ['"Segoe UI Variable"', 'Segoe UI', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(15, 35, 63, 0.06)',
        lift: '0 18px 40px rgba(15, 35, 63, 0.12)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.3s ease both',
      },
    },
  },
  plugins: [],
};
