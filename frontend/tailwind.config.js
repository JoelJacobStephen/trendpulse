/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./public/index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3c6e71',
        secondary: '#d9d9d9',
        text: '#353535',
        light: '#f5f5f5',
        accent: '#d62828',
      },
      fontFamily: {
        'serif': ['Playfair Display', 'serif'],
        'sans': ['Source Sans Pro', 'sans-serif'],
      },
    },
  },
  plugins: [],
  safelist: [
    'bg-primary',
    'text-primary',
    'border-primary',
    'bg-secondary',
    'border-secondary',
    'text-accent',
    'bg-light'
  ]
}
