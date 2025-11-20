/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'schiro-yellow': '#f6c21a',
        'schiro-blue': '#39a4ff',
        'schiro-pink': '#ff6ec7',
        'schiro-green': '#7ac943',
        'schiro-orange': '#ffa221',
        'schiro-orange-strong': '#ff8a00',
        'schiro-bg': '#fff9e8',
        'schiro-ink': '#1d1d1f',
      },
      fontFamily: {
        'chewy': ['Chewy', 'cursive'],
        'nunito': ['Nunito', 'system-ui'],
      },
    },
  },
  plugins: [],
}
