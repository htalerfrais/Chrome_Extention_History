/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', 'Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'],
      },
      colors: {
        bg: '#000000',
        card: '#111111',
        surface: '#080808',
        text: '#ffffff',
        muted: '#9ca3af',
        accent: '#3b82f6',
        'accent-hover': '#60a5fa',
        border: 'rgba(255, 255, 255, 0.1)',
      },
    },
  },
  plugins: [],
}
