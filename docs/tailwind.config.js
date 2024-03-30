/** @type {import('tailwindcss').Config} */
module.exports = {
  content: {
    files: [
      "./inputs/*.yml",
      "./partials/*.html",
      "./index.html"
    ],
    relative: true,
  },
  theme: {},
  plugins: [],
  minify: true
}