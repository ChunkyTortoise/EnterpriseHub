/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './components/**/*.{js,jsx,ts,tsx}',
    './pages/**/*.{js,jsx,ts,tsx}',
    './app/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      animation: {
        'slide-up': 'slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        'fade-in-delay': 'fadeInDelay 3s ease-in-out forwards',
        'bounce': 'bounce 1s ease-in-out infinite',
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite',
      },
      keyframes: {
        slideUp: {
          'from': {
            transform: 'translateY(100%)',
            opacity: '0',
          },
          'to': {
            transform: 'translateY(0)',
            opacity: '1',
          },
        },
        fadeInDelay: {
          '0%': { opacity: '0' },
          '50%': { opacity: '0' },
          '100%': { opacity: '0.6' },
        },
        bounce: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%, 100%': { 
            boxShadow: '0 0 20px rgba(34, 197, 94, 0.5)' 
          },
          '50%': { 
            boxShadow: '0 0 40px rgba(34, 197, 94, 0.8)' 
          },
        },
      },
      colors: {
        // Custom brand colors (optional)
        brand: {
          primary: '#3B82F6',
          secondary: '#10B981',
          accent: '#F59E0B',
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
