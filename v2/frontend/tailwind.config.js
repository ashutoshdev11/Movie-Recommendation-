/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cosmic: {
          950: '#030712',
          900: '#070b19',
          850: '#0b112c',
          800: '#0f1738',
          700: '#1e295d',
        },
        hologram: {
          cyan: '#00f2fe',
          teal: '#4facfe',
          violet: '#8a2be2',
          purple: '#b829dd',
          pink: '#ff2a85',
        },
      },
      boxShadow: {
        'neon-cyan': '0 0 20px -2px rgba(0, 242, 254, 0.4), 0 0 40px -10px rgba(0, 242, 254, 0.2)',
        'neon-violet': '0 0 20px -2px rgba(184, 41, 221, 0.4), 0 0 40px -10px rgba(184, 41, 221, 0.2)',
        'hologram': '0 8px 32px 0 rgba(0, 242, 254, 0.15)',
        'card-hover': '0 20px 40px -15px rgba(0, 242, 254, 0.35)',
      },
      backgroundImage: {
        'cosmic-gradient': 'radial-gradient(ellipse at top, #0f1738 0%, #070b19 50%, #030712 100%)',
        'holo-gradient': 'linear-gradient(135deg, rgba(0, 242, 254, 0.2) 0%, rgba(184, 41, 221, 0.15) 100%)',
        'card-glass': 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
      },
      animation: {
        float: 'float 4s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
