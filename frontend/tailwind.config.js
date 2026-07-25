/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // supports dark themes
  theme: {
    extend: {
      colors: {
        brand: {
          background: '#000000',
          surface: '#050505',
          surfaceElevated: '#0B0C10',
          border: '#15181F',
          borderHover: '#222831',
          text: '#F3F4F6',
          textSecondary: '#9CA3AF',
          textMuted: '#6B7280',
          primary: '#10B981',
          primaryHover: '#059669',
          accent: '#34D399',
          glowPrimary: 'rgba(16, 185, 129, 0.12)',
          glowAccent: 'rgba(52, 211, 153, 0.12)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Geist', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'aurora': 'aurora 25s infinite alternate ease-in-out',
        'grid-glow': 'grid-glow 8s infinite linear',
        'float-orb-1': 'float-orb-1 20s infinite ease-in-out',
        'float-orb-2': 'float-orb-2 25s infinite ease-in-out',
        'shimmer': 'shimmer 2.5s infinite linear',
        'fade-in-up': 'fade-in-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'scale-up': 'scale-up 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'typing': 'typing 1.4s infinite',
      },
      keyframes: {
        aurora: {
          '0%': { transform: 'translate(0px, 0px) rotate(0deg)' },
          '50%': { transform: 'translate(100px, 80px) rotate(180deg)' },
          '100%': { transform: 'translate(-50px, -40px) rotate(360deg)' },
        },
        'grid-glow': {
          '0%': { 'background-position': '0% 0%' },
          '100%': { 'background-position': '0% 100%' },
        },
        'float-orb-1': {
          '0%, 100%': { transform: 'translate(0px, 0px) scale(1)' },
          '33%': { transform: 'translate(30px, -50px) scale(1.15)' },
          '66%': { transform: 'translate(-20px, 20px) scale(0.9)' },
        },
        'float-orb-2': {
          '0%, 100%': { transform: 'translate(0px, 0px) scale(1)' },
          '50%': { transform: 'translate(-40px, 40px) scale(1.2)' },
        },
        shimmer: {
          '0%': { 'background-position': '-200% 0' },
          '100%': { 'background-position': '200% 0' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-up': {
          '0%': { opacity: '0', transform: 'scale(0.96)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        typing: {
          '0%, 100%': { opacity: '0.2' },
          '50%': { opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
