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
        // Professional corporate brand colors: rich deep slate and cool energetic cyan/blue
        brand: {
          background: '#0B0F19',
          surface: '#161F30',
          border: '#23334C',
          text: '#F3F4F6',
          primary: '#3B82F6',
          primaryHover: '#2563EB',
          accent: '#06B6D4',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
