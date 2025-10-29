/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  important: true, // Critical for Chrome Extension CSP compatibility
  theme: {
    extend: {
      colors: {
        bg: '#0b1220',
        card: '#0f1b2d',
        text: '#f3f4f6',
        muted: 'rgba(243, 244, 246, 0.72)',
        accent: '#c9a227',
        'accent-hover': '#e0ba3a',
        border: 'rgba(201, 162, 39, 0.28)',
        'input-bg': 'rgba(255, 255, 255, 0.04)',
        'glass-bg': 'rgba(15, 27, 45, 0.82)',
        'glass-border': 'rgba(201, 162, 39, 0.18)',
      },
      boxShadow: {
        light: '0 4px 20px rgba(0, 0, 0, 0.25)',
        medium: '0 10px 36px rgba(0, 0, 0, 0.35)',
        heavy: '0 18px 60px rgba(0, 0, 0, 0.5)',
      },
      backgroundImage: {
        'gradient-accent': 'linear-gradient(135deg, #b8891f 0%, #e0ba3a 100%)',
        'gradient-card': 'linear-gradient(145deg, rgba(15, 27, 45, 0.95) 0%, rgba(15, 27, 45, 0.85) 100%)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}

