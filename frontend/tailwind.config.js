/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#EEF1EE",
        ink: "#1E2528",
        graphite: "#566064",
        rule: "#D6DCD7",
        brand: { DEFAULT: "#1D5B47", dark: "#123D30" },
        highlight: "#F5E27C",
      },
      fontFamily: {
        serif: ["Newsreader", "Georgia", "serif"],
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
