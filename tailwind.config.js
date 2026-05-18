/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
    "./node_modules/flowbite/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        "osu-navy": "#002147",
        "osu-orange": "#D73F09",
        "osu-lavender": "#BBA0CA",
        "osu-blue-light": "#a2ceff",
      },
    },
  },
  plugins: [
    require("flowbite/plugin"),
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
};