/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'pastel-green': '#BFE3C0',
        'pastel-beige': '#F5EDE1',
        'pastel-yellow': '#FFF3B0',
        'forest': '#2E6B57',
        'sand': '#EADBC8',
        'lemon': '#FFE79A',
        'ink': '#2F3B2F',
      },
    },
  },
  plugins: [],
}
