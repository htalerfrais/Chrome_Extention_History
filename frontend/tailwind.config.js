/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'],
      },
      colors: {
        // Background layers (dark navy progression)
        bg: {
          DEFAULT: '#0B0D13',
          deep: '#070810',
          raised: '#10131A',
          elevated: '#161923',
        },
        // Surfaces (for cards, panels, inputs)
        surface: {
          DEFAULT: '#1C1F2B',
          hover: '#222634',
          active: '#282D3E',
        },
        // Text hierarchy
        text: {
          DEFAULT: '#E8EAED',
          secondary: '#9BA1B0',
          tertiary: '#5F6575',
          ghost: '#3D4255',
        },
        // Accent (indigo)
        accent: {
          DEFAULT: '#6366F1',
          hover: '#818CF8',
          muted: 'rgba(99, 102, 241, 0.15)',
          subtle: 'rgba(99, 102, 241, 0.08)',
        },
        // Borders
        line: {
          DEFAULT: 'rgba(255, 255, 255, 0.06)',
          strong: 'rgba(255, 255, 255, 0.10)',
          accent: 'rgba(99, 102, 241, 0.3)',
        },
        // Semantic
        error: '#EF4444',
        success: '#22C55E',
      },
      borderRadius: {
        DEFAULT: '6px',
        lg: '8px',
        xl: '12px',
      },
      fontSize: {
        'xxs': ['0.625rem', { lineHeight: '0.875rem' }],  // 10px
      },
    },
  },
  plugins: [],
}
