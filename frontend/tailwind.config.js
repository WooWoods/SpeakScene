/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17211b",
        moss: "#49624c",
        leaf: "#2f7d5a",
        coral: "#da6b55",
        skyglass: "#e8f3f5",
        paper: "#fffdf8",
      },
      boxShadow: {
        panel: "0 18px 60px rgba(23, 33, 27, 0.10)",
      },
    },
  },
  plugins: [],
}
